#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


def size(page) -> tuple[float, float]:
    return float(page.mediabox.width), float(page.mediabox.height)


def require_glyphs_inside(path: Path, label: str) -> None:
    with pdfplumber.open(path) as doc:
        for page_number, page in enumerate(doc.pages, 1):
            for char in page.chars:
                if (
                    float(char["x0"]) < -0.1
                    or float(char["x1"]) > page.width + 0.1
                    or float(char["top"]) < -0.1
                    or float(char["bottom"]) > page.height + 0.1
                ):
                    raise SystemExit(f"{label} glyph outside page {page_number}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewed_map", type=Path)
    parser.add_argument("semantic_audit", type=Path)
    parser.add_argument("translated", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("final", type=Path)
    parser.add_argument("output_report", type=Path)
    parser.add_argument("--gutter", type=float, default=12.0)
    parser.add_argument("--visual-inspection", choices=("passed",), required=True)
    args = parser.parse_args()

    map_bytes = args.reviewed_map.read_bytes()
    translations = json.loads(map_bytes)["translations"]
    audit = json.loads(args.semantic_audit.read_text(encoding="utf-8"))
    digest = hashlib.sha256(map_bytes).hexdigest()
    if audit.get("status") != "passed":
        raise SystemExit("semantic audit did not pass")
    if audit.get("reviewed_segments") != len(translations):
        raise SystemExit("semantic audit segment count mismatch")
    if audit.get("translation_map_sha256") != digest:
        raise SystemExit("reviewed map changed after semantic audit")

    translated = PdfReader(str(args.translated))
    source = PdfReader(str(args.source))
    final = PdfReader(str(args.final))
    if not (len(translated.pages) == len(source.pages) == len(final.pages)):
        raise SystemExit(
            f"page mismatch: translated={len(translated.pages)} "
            f"source={len(source.pages)} final={len(final.pages)}"
        )
    for page_number, (jp, en, spread) in enumerate(
        zip(translated.pages, source.pages, final.pages), 1
    ):
        jp_w, jp_h = size(jp)
        en_w, en_h = size(en)
        out_w, out_h = size(spread)
        if abs(out_w - (jp_w + args.gutter + en_w)) > 0.02:
            raise SystemExit(f"spread width mismatch on page {page_number}")
        if abs(out_h - max(jp_h, en_h)) > 0.02:
            raise SystemExit(f"spread height mismatch on page {page_number}")

    require_glyphs_inside(args.translated, "translated")
    require_glyphs_inside(args.final, "final")
    report = {
        "status": "passed",
        "semantic_audit": "passed",
        "visual_inspection": args.visual_inspection,
        "reviewed_segments": len(translations),
        "pages": len(final.pages),
        "layout": "Japanese-left/source-right",
        "gutter_points": args.gutter,
        "glyph_overflow": "none",
        "translation_map_sha256": digest,
        "final_pdf_sha256": hashlib.sha256(args.final.read_bytes()).hexdigest(),
    }
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
