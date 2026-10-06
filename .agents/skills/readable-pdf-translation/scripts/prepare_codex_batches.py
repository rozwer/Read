#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--batches", type=int, default=3)
    args = parser.parse_args()
    items = json.loads(args.segments.read_text(encoding="utf-8"))["segments"]
    target = sum(len(item["source"]) for item in items) / args.batches
    batches = [[]]
    chars = 0
    contextual_items = []
    for index, item in enumerate(items):
        contextual_items.append(
            {
                **item,
                "context_before": [
                    x["source"] for x in items[max(0, index - 2) : index]
                ],
                "context_after": [
                    x["source"] for x in items[index + 1 : index + 3]
                ],
            }
        )
    for item in contextual_items:
        if len(batches) < args.batches and batches[-1] and chars + len(item["source"]) > target:
            batches.append([])
            chars = 0
        batches[-1].append(item)
        chars += len(item["source"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for number, batch in enumerate(batches, 1):
        (args.output_dir / f"batch-{number:03d}.json").write_text(
            json.dumps({"items": batch}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(" ".join(f"batch-{i + 1:03d}={len(batch)}" for i, batch in enumerate(batches)))


if __name__ == "__main__":
    main()
