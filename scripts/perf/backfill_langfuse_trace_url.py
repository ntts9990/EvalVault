"""Backfill Langfuse trace_url into evaluation_runs metadata."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from evalvault.config.settings import Settings


def _parse_log_file(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    current_run_id: str | None = None

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if "Run ID:" in line:
            parts = line.split("Run ID:")
            if len(parts) > 1:
                candidate = parts[-1].strip().strip("│").strip()
                if candidate:
                    current_run_id = candidate
        if "Logged to Langfuse" in line and "trace_id:" in line:
            start = line.find("trace_id:")
            if start != -1:
                trace_id = line[start + len("trace_id:") :].strip().strip(")")
                if current_run_id and trace_id:
                    mapping[current_run_id] = trace_id
    return mapping


def _load_metadata(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _ensure_langfuse_meta(metadata: dict[str, Any]) -> dict[str, Any]:
    langfuse_meta = metadata.get("langfuse")
    if not isinstance(langfuse_meta, dict):
        langfuse_meta = {}
    return langfuse_meta


def _update_db(
    db_path: Path,
    trace_map: dict[str, str],
    *,
    langfuse_client,
    host: str,
    dry_run: bool,
) -> int:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    updated = 0

    try:
        table_row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_runs'"
        ).fetchone()
        if table_row is None:
            conn.close()
            return -1

        columns = {row[1] for row in conn.execute("PRAGMA table_info(evaluation_runs)").fetchall()}
        if "metadata" not in columns:
            conn.close()
            return -2

        select_cols = ["run_id", "metadata"]
        has_trace_column = "langfuse_trace_id" in columns
        if has_trace_column:
            select_cols.append("langfuse_trace_id")

        rows = conn.execute(f"SELECT {', '.join(select_cols)} FROM evaluation_runs").fetchall()
    except sqlite3.Error:
        conn.close()
        return -3

    for row in rows:
        run_id = row["run_id"]
        metadata = _load_metadata(row["metadata"])
        langfuse_meta = _ensure_langfuse_meta(metadata)

        trace_id = langfuse_meta.get("trace_id")
        if not trace_id:
            if "langfuse_trace_id" in row:
                trace_id = row["langfuse_trace_id"] or trace_map.get(run_id)
            else:
                trace_id = trace_map.get(run_id)
        if not trace_id:
            continue

        changed = False
        if langfuse_meta.get("trace_id") != trace_id:
            langfuse_meta["trace_id"] = trace_id
            changed = True
        if not langfuse_meta.get("host"):
            langfuse_meta["host"] = host
            changed = True
        if not langfuse_meta.get("trace_url"):
            trace_url = None
            try:
                trace_url = langfuse_client.get_trace_url(trace_id=trace_id)
            except Exception:
                trace_url = None
            if trace_url:
                langfuse_meta["trace_url"] = trace_url
                changed = True

        if changed:
            metadata["langfuse"] = langfuse_meta
            if not dry_run:
                if "langfuse_trace_id" in row:
                    conn.execute(
                        "UPDATE evaluation_runs SET metadata = ?, langfuse_trace_id = ? WHERE run_id = ?",
                        (json.dumps(metadata, ensure_ascii=True), trace_id, run_id),
                    )
                else:
                    conn.execute(
                        "UPDATE evaluation_runs SET metadata = ? WHERE run_id = ?",
                        (json.dumps(metadata, ensure_ascii=True), run_id),
                    )
            updated += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill Langfuse trace_url into evaluation_runs metadata."
    )
    parser.add_argument("db", nargs="+", help="SQLite DB path(s) to update.")
    parser.add_argument(
        "--log",
        action="append",
        default=[],
        help="Optional run log path(s) to extract run_id -> trace_id mapping.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report only, no updates.")
    args = parser.parse_args()

    settings = Settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        print("LANGFUSE_PUBLIC_KEY/SECRET_KEY not set.")
        return 1

    from langfuse import Langfuse

    client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )

    trace_map: dict[str, str] = {}
    for log_path in args.log:
        path = Path(log_path)
        if not path.exists():
            print(f"[skip] log not found: {path}")
            continue
        trace_map.update(_parse_log_file(path))

    total_updates = 0
    for db_path in args.db:
        path = Path(db_path)
        if not path.exists():
            print(f"[skip] db not found: {path}")
            continue
        updates = _update_db(
            path,
            trace_map,
            langfuse_client=client,
            host=settings.langfuse_host,
            dry_run=args.dry_run,
        )
        if updates < 0:
            if updates == -1:
                print(f"[skip] {path}: missing evaluation_runs table")
            elif updates == -2:
                print(f"[skip] {path}: evaluation_runs missing metadata column")
            else:
                print(f"[skip] {path}: sqlite error")
            continue
        total_updates += updates
        print(f"[ok] {path}: updated {updates} run(s)")

    if args.dry_run:
        print("dry-run: no changes written")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
