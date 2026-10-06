#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_translations(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["translations"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("translation_map", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--batches", type=int, default=3)
    args = parser.parse_args()
    if args.batches < 1:
        raise SystemExit("batches must be positive")

    segments = json.loads(args.segments.read_text(encoding="utf-8"))["segments"]
    translations = load_translations(args.translation_map)
    if [x["id"] for x in segments] != [x["id"] for x in translations]:
        raise SystemExit("segment/translation order mismatch")

    packets = []
    for index, (segment, translation) in enumerate(zip(segments, translations)):
        if segment["source"] != translation["source"]:
            raise SystemExit(f"source mismatch: {segment['id']}")
        packets.append(
            {
                "id": segment["id"],
                "source": segment["source"],
                "translation": translation["text"],
                "previous": (
                    {
                        "id": segments[index - 1]["id"],
                        "source": segments[index - 1]["source"],
                        "translation": translations[index - 1]["text"],
                    }
                    if index
                    else None
                ),
                "next": (
                    {
                        "id": segments[index + 1]["id"],
                        "source": segments[index + 1]["source"],
                        "translation": translations[index + 1]["text"],
                    }
                    if index + 1 < len(segments)
                    else None
                ),
                "context_window": [
                    {
                        "id": segments[position]["id"],
                        "source": segments[position]["source"],
                        "translation": translations[position]["text"],
                    }
                    for position in range(max(0, index - 2), min(len(segments), index + 3))
                    if position != index
                ],
            }
        )

    target = sum(len(x["source"]) for x in packets) / args.batches
    batches: list[list[dict]] = [[]]
    chars = 0
    for packet in packets:
        if len(batches) < args.batches and batches[-1] and chars + len(packet["source"]) > target:
            batches.append([])
            chars = 0
        batches[-1].append(packet)
        chars += len(packet["source"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for number, batch in enumerate(batches, 1):
        path = args.output_dir / f"review-{number:03d}.json"
        path.write_text(json.dumps({"items": batch}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(" ".join(f"review-{i + 1:03d}={len(batch)}" for i, batch in enumerate(batches)))


if __name__ == "__main__":
    main()
