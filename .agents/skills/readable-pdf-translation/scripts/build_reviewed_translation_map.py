#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


PLACEHOLDER = re.compile(r"\{v\d+\}")
URL = re.compile(r"https?://\S+")
CHECKS = (
    "meaning_complete",
    "no_additions",
    "terminology",
    "protected_tokens",
    "variable_roles",
    "cross_segment_continuity",
)


def ordered_subsequence(needles: list[str], haystack: list[str]) -> bool:
    position = 0
    for needle in needles:
        try:
            position = haystack.index(needle, position) + 1
        except ValueError:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("translation_map", type=Path)
    parser.add_argument("reviews_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    segments = json.loads(args.segments.read_text(encoding="utf-8"))["segments"]
    originals = json.loads(args.translation_map.read_text(encoding="utf-8"))["translations"]
    if [x["id"] for x in segments] != [x["id"] for x in originals]:
        raise SystemExit("segment/translation order mismatch")
    original_by_id = {x["id"]: x for x in originals}

    reviews: dict[str, dict] = {}
    for path in sorted(args.reviews_dir.glob("*.json")):
        for item in json.loads(path.read_text(encoding="utf-8"))["reviews"]:
            if item["id"] in reviews:
                raise SystemExit(f"duplicate review: {item['id']}")
            reviews[item["id"]] = item

    expected_ids = {x["id"] for x in segments}
    if expected_ids != reviews.keys():
        raise SystemExit(
            f"review ID mismatch: missing={len(expected_ids - reviews.keys())} "
            f"extra={len(reviews.keys() - expected_ids)}"
        )

    final = []
    revised = 0
    for segment in segments:
        item = reviews[segment["id"]]
        original = original_by_id[segment["id"]]
        if item.get("source") != segment["source"]:
            raise SystemExit(f"review source mismatch: {segment['id']}")
        if item.get("original_text") != original["text"]:
            raise SystemExit(f"review original mismatch: {segment['id']}")
        checks = item.get("checks", {})
        failed = [name for name in CHECKS if checks.get(name) is not True]
        if failed:
            raise SystemExit(f"unresolved review checks: {segment['id']} {','.join(failed)}")
        text = item.get("final_text", "")
        if not text.strip():
            raise SystemExit(f"empty reviewed translation: {segment['id']}")
        if PLACEHOLDER.findall(segment["source"]) != PLACEHOLDER.findall(text):
            raise SystemExit(f"placeholder order mismatch after review: {segment['id']}")
        if not ordered_subsequence(URL.findall(segment["source"]), URL.findall(text)):
            raise SystemExit(f"URL mismatch after review: {segment['id']}")
        revised += text != original["text"]
        final.append({"id": segment["id"], "source": segment["source"], "text": text})

    payload = {"translations": final}
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    report = {
        "status": "passed",
        "reviewed_segments": len(final),
        "revised_segments": revised,
        "required_checks": list(CHECKS),
        "translation_map_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
