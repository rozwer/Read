#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDER = re.compile(r"\{v\d+\}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("translations_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    segments = json.loads(args.segments.read_text(encoding="utf-8"))["segments"]
    expected = {item["id"]: item["source"] for item in segments}
    translated = {}
    for path in sorted(args.translations_dir.glob("*.json")):
        for item in json.loads(path.read_text(encoding="utf-8"))["translations"]:
            if item["id"] in translated:
                raise SystemExit(f"duplicate ID: {item['id']}")
            translated[item["id"]] = item

    if expected.keys() != translated.keys():
        raise SystemExit(
            f"ID mismatch: missing={len(expected.keys() - translated.keys())} "
            f"extra={len(translated.keys() - expected.keys())}"
        )
    for segment_id, source in expected.items():
        item = translated[segment_id]
        if item["source"] != source:
            raise SystemExit(f"source mismatch: {segment_id}")
        if PLACEHOLDER.findall(source) != PLACEHOLDER.findall(item["text"]):
            raise SystemExit(f"placeholder order mismatch: {segment_id}")
        if not item["text"].strip():
            raise SystemExit(f"empty translation: {segment_id}")

    output = {"translations": [translated[item["id"]] for item in segments]}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"translations={len(segments)} placeholders=valid source_keys=valid")


if __name__ == "__main__":
    main()
