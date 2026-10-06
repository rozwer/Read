#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("translation_map", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    segments = json.loads(args.segments.read_text(encoding="utf-8"))["segments"]
    translations = json.loads(args.translation_map.read_text(encoding="utf-8"))["translations"]
    report = {
        "measurement": "translation payload characters; not billed token usage",
        "segments": len(segments),
        "source_characters": sum(len(item["source"]) for item in segments),
        "translation_characters": sum(len(item["text"]) for item in translations),
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
