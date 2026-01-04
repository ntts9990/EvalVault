#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install via https://github.com/astral-sh/uv" >&2
  exit 1
fi

uv run python - <<'PY'
missing = []
for pkg in ("kiwipiepy", "rank_bm25"):
    try:
        __import__(pkg)
    except Exception:
        missing.append(pkg)
if missing:
    raise SystemExit(
        "Missing Korean retriever deps: "
        + ", ".join(missing)
        + " (install with `uv sync --extra korean`)"
    )
PY

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/evalvault-r1-smoke.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT

DATASET_PATH="${WORKDIR}/dataset.json"
DOCS_PATH="${ROOT_DIR}/examples/benchmarks/korean_rag/retrieval_test.json"
DB_PATH="${WORKDIR}/evalvault.db"
OUTPUT_PATH="${WORKDIR}/run.json"
PROMPT_PATH="${WORKDIR}/prompt.txt"
PROMPT_MANIFEST_PATH="${WORKDIR}/prompt_manifest.json"

# Korean text ensures Kiwi BM25 tokenization hits known insurance terms.
cat > "$DATASET_PATH" <<'JSON'
{
  "name": "retriever-smoke",
  "version": "1.0.0",
  "test_cases": [
    {
      "id": "tc-1",
      "question": "보험료는 얼마인가요?",
      "answer": "보험료는 월 15만원입니다.",
      "contexts": []
    }
  ]
}
JSON

cat > "$PROMPT_PATH" <<'PROMPT'
당신은 보험 약관 QA를 돕는 도우미입니다.
PROMPT

uv run python - <<'PY' "$PROMPT_PATH" "$PROMPT_MANIFEST_PATH"
import json
import sys
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

prompt_path = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2])
content = prompt_path.read_text(encoding="utf-8")
checksum = sha256(content.encode("utf-8")).hexdigest()

manifest = {
    "version": 1,
    "updated_at": datetime.now(UTC).isoformat(),
    "prompts": {
        prompt_path.as_posix(): {
            "checksum": checksum,
            "last_synced_at": datetime.now(UTC).isoformat(),
            "content": content,
        }
    },
}

manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY

uv run evalvault run "$DATASET_PATH" \
  --profile dev \
  --metrics insurance_term_accuracy \
  --retriever bm25 \
  --retriever-docs "$DOCS_PATH" \
  --retriever-top-k 2 \
  --prompt-manifest "$PROMPT_MANIFEST_PATH" \
  --prompt-files "$PROMPT_PATH" \
  --db "$DB_PATH" \
  --stage-store \
  --output "$OUTPUT_PATH"

RUN_ID="$(python3 - <<'PY' "$OUTPUT_PATH"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
run_id = payload.get("run_id", "")
if not run_id:
    raise SystemExit("run_id missing from output JSON")
print(run_id)
PY
)"

uv run evalvault stage report "$RUN_ID" --db "$DB_PATH"

echo "R1 smoke run complete."
echo "Artifacts stored in: $WORKDIR"
