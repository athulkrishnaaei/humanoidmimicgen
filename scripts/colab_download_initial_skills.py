#!/usr/bin/env python3
"""Download the two HMG task datasets in Colab and archive them to Drive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

from verify_initial_skills_data import TASKS, verify


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_REPO = "linkenv/humanoidmimicgen-g1-benchmark"
DATASET_REVISION = "acf6b53853dd0199bf852286ca68067cc37472ff"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_and_archive(task: str, drive_dir: Path) -> Path:
    archive = drive_dir / f"{task}.tar"
    checksum_path = drive_dir / f"{task}.tar.sha256"
    manifest_path = drive_dir / f"{task}.manifest.json"
    partial = drive_dir / f"{task}.tar.partial"
    if archive.exists():
        if not checksum_path.is_file():
            raise FileExistsError(f"Archive exists without checksum: {archive}")
        expected = checksum_path.read_text().split()[0]
        if sha256_file(archive) != expected:
            raise ValueError(f"Existing archive checksum does not match: {archive}")
        print(f"Already verified: {archive}", flush=True)
        return archive
    if partial.exists():
        raise FileExistsError(f"Incomplete archive needs inspection: {partial}")

    # Temporary Colab storage is removed after the Drive archive and checksum
    # are complete; the Drive copy is retained.
    with tempfile.TemporaryDirectory(prefix=f"hmg-{task}-", dir="/content") as temp:
        source_root = Path(temp) / "source"
        subprocess.run(
            [
                "bash",
                str(REPO_ROOT / "scripts" / "download_initial_skills_data.sh"),
                str(source_root),
                task,
            ],
            cwd=REPO_ROOT,
            check=True,
        )
        episodes, parquet_files, videos = verify(source_root, task)
        task_root = source_root / "datasets" / task
        with tarfile.open(partial, "w") as out:
            out.add(task_root, arcname=f"datasets/{task}")
        checksum = sha256_file(partial)
        partial.rename(archive)
        checksum_path.write_text(f"{checksum}  {archive.name}\n")
        manifest_path.write_text(
            json.dumps(
                {
                    "task": task,
                    "dataset_repository": DATASET_REPO,
                    "revision": DATASET_REVISION,
                    "episodes": episodes,
                    "parquet_files": parquet_files,
                    "ego_videos": videos,
                    "archive": archive.name,
                    "sha256": checksum,
                },
                indent=2,
            )
            + "\n"
        )
    print(f"Saved {archive} ({archive.stat().st_size / 1e9:.2f} GB)", flush=True)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument(
        "--drive-dir",
        type=Path,
        default=Path("/content/drive/MyDrive/HumanoidMimicGen-initial-skills"),
    )
    args = parser.parse_args()

    try:
        from google.colab import drive
    except ImportError as exc:
        raise SystemExit("Run this script in Google Colab.") from exc
    drive.mount("/content/drive")
    drive_dir = args.drive_dir.expanduser().resolve()
    if not str(drive_dir).startswith("/content/drive/MyDrive/"):
        raise ValueError("--drive-dir must be inside your mounted MyDrive")
    drive_dir.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage("/content").free / 1e9
    print(f"Temporary Colab disk free: {free_gb:.1f} GB", flush=True)
    for task in dict.fromkeys(args.tasks):
        download_and_archive(task, drive_dir)


if __name__ == "__main__":
    main()
