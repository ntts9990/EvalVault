from __future__ import annotations

import argparse
import os
from pathlib import Path

DEFAULT_HF_MODELS = [
    "dragonkue/BGE-m3-ko",
    "upskyy/bge-m3-korean",
    "BAAI/bge-m3",
    "jhgan/ko-sroberta-multitask",
    "intfloat/multilingual-e5-large",
]


def _split_models(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _predownload_hf(models: list[str], hf_cache: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit(
            "huggingface_hub is not installed. Install with 'uv add huggingface_hub'."
        ) from exc

    _ensure_dir(hf_cache)
    for model in models:
        snapshot_download(
            repo_id=model,
            cache_dir=str(hf_cache),
            resume_download=True,
        )


def _predownload_sentence_transformers(models: list[str]) -> None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "sentence-transformers is not installed. Install with 'uv add sentence-transformers'."
        ) from exc

    for model in models:
        SentenceTransformer(model)


def _predownload_kiwi() -> None:
    try:
        from kiwipiepy import Kiwi
    except ImportError as exc:
        raise SystemExit("kiwipiepy is not installed. Install with 'uv add kiwipiepy'.") from exc

    Kiwi()


def main() -> int:
    parser = argparse.ArgumentParser(description="Predownload NLP models for offline use.")
    parser.add_argument(
        "--models",
        default=None,
        help="Comma-separated HuggingFace model list. Defaults to Korean NLP set.",
    )
    parser.add_argument(
        "--cache-root",
        default="model_cache",
        help="Root directory to store caches (HF + sentence-transformers).",
    )
    parser.add_argument(
        "--skip-sentence-transformers",
        action="store_true",
        help="Skip SentenceTransformer download (HF cache only).",
    )
    parser.add_argument(
        "--include-kiwi",
        action="store_true",
        help="Warm Kiwi tokenizer cache (requires kiwipiepy).",
    )

    args = parser.parse_args()

    models = _split_models(args.models) or list(DEFAULT_HF_MODELS)
    cache_root = Path(args.cache_root).resolve()

    hf_cache = cache_root / "hf"
    st_cache = cache_root / "sentence-transformers"

    os.environ.setdefault("HF_HOME", str(hf_cache))
    os.environ.setdefault("HF_HUB_CACHE", str(hf_cache / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_cache / "hub"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(st_cache))

    _predownload_hf(models, hf_cache)

    if not args.skip_sentence_transformers:
        _predownload_sentence_transformers(models)

    if args.include_kiwi:
        _predownload_kiwi()

    print("Downloaded models:")
    for model in models:
        print(f"- {model}")
    print(f"Cache root: {cache_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
