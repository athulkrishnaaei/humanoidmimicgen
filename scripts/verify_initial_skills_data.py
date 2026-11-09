#!/usr/bin/env python3
"""Check transferred HumanoidMimicGen task snapshots before offline training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TASKS = ("04_push_shelf_forward", "07_box_table_to_shelf")


def verify(root: Path, task: str) -> tuple[int, int, int]:
    if task not in TASKS:
        raise ValueError(f"Unsupported initial skill: {task}")
    task_root = root / "datasets" / task
    episodes = parquet_total = video_total = 0
    problems: list[str] = []
    for index in range(8):
        shard = task_root / f"shard_{index:03d}"
        info_path = shard / "meta" / "info.json"
        stats_path = shard / "meta" / "stats.json"
        if not info_path.is_file() or not stats_path.is_file():
            problems.append(f"{shard.name}: missing info.json or stats.json")
            continue
        info = json.loads(info_path.read_text())
        expected = info.get("total_episodes")
        if not isinstance(expected, int) or expected < 1:
            problems.append(f"{shard.name}: invalid total_episodes")
            continue
        parquet_count = sum(1 for _ in (shard / "data").rglob("*.parquet"))
        video_count = sum(
            1
            for path in (shard / "videos").rglob("*.mp4")
            if "observation.images.ego_view" in path.parts
        )
        if parquet_count != expected or video_count != expected:
            problems.append(
                f"{shard.name}: expected {expected} episodes, found "
                f"{parquet_count} parquet files and {video_count} ego videos"
            )
        episodes += expected
        parquet_total += parquet_count
        video_total += video_count
    if problems:
        raise ValueError(f"Incomplete {task} snapshot:\n" + "\n".join(problems))
    return episodes, parquet_total, video_total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="snapshot root containing datasets/")
    parser.add_argument("--task", choices=TASKS, action="append", required=True)
    args = parser.parse_args()
    for task in args.task:
        counts = verify(args.root.expanduser().resolve(), task)
        print(f"{task}: verified {counts[0]} episodes, {counts[1]} parquet files, {counts[2]} ego videos")
