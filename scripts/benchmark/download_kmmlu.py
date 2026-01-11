#!/usr/bin/env python3
"""Download KMMLU dataset for offline/airgapped environments.

Usage (external network):
    python scripts/benchmark/download_kmmlu.py --subjects Insurance Finance

Usage (airgapped - after copying the tar.gz):
    python scripts/benchmark/download_kmmlu.py --load-local --input kmmlu_download.tar.gz
"""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("data/benchmarks/kmmlu")
DEFAULT_SUBJECTS = ["Insurance"]


def download_subjects(
    subjects: list[str],
    output_dir: Path,
    create_archive: bool = True,
) -> Path:
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("Install datasets: pip install datasets") from e

    output_dir.mkdir(parents=True, exist_ok=True)

    for subject in subjects:
        print(f"Downloading KMMLU/{subject}...")
        ds = load_dataset("HAERAE-HUB/KMMLU", subject, trust_remote_code=True)
        subject_dir = output_dir / subject.lower().replace(" ", "_")
        ds.save_to_disk(str(subject_dir))
        print(f"  Saved to {subject_dir}")

    if create_archive:
        archive_path = output_dir.parent / "kmmlu_download.tar.gz"
        print(f"Creating archive: {archive_path}")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(output_dir, arcname=output_dir.name)
        print("Archive created. Transfer this file to airgapped environment.")
        return archive_path

    return output_dir


def extract_archive(archive_path: Path, output_dir: Path) -> None:
    print(f"Extracting {archive_path} to {output_dir.parent}")
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=output_dir.parent)
    print(f"Extracted to {output_dir}")


def load_local_dataset(subject_dir: Path) -> dict:
    try:
        from datasets import load_from_disk
    except ImportError as e:
        raise ImportError("Install datasets: pip install datasets") from e

    print(f"Loading from {subject_dir}")
    ds = load_from_disk(str(subject_dir))
    print(f"  Loaded {len(ds)} splits")
    return {"dataset": ds, "path": subject_dir}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download KMMLU for offline use")
    parser.add_argument(
        "--subjects",
        nargs="+",
        default=DEFAULT_SUBJECTS,
        help="KMMLU subjects to download (e.g., Insurance Finance)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory",
    )
    parser.add_argument(
        "--load-local",
        action="store_true",
        help="Load from local archive instead of downloading",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Input archive path (for --load-local)",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Don't create tar.gz archive after download",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify loaded dataset by printing sample",
    )

    args = parser.parse_args()

    if args.load_local:
        if args.input:
            extract_archive(args.input, args.output_dir)

        for subject in args.subjects:
            subject_dir = args.output_dir / subject.lower().replace(" ", "_")
            if subject_dir.exists():
                result = load_local_dataset(subject_dir)
                if args.verify:
                    ds = result["dataset"]
                    if "test" in ds:
                        print(f"  Sample: {ds['test'][0]}")
    else:
        download_subjects(
            args.subjects,
            args.output_dir,
            create_archive=not args.no_archive,
        )


if __name__ == "__main__":
    main()
