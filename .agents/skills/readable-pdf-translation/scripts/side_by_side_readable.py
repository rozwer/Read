#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber
from pypdf import PageObject, PdfReader, PdfWriter, Transformation


def dimensions(page) -> tuple[float, float, float, float]:
    box = page.mediabox
    return float(box.left), float(box.bottom), float(box.width), float(box.height)


def translated_overflow(path: Path) -> tuple[float, float, list[int]]:
    max_left = 0.0
    max_right = 0.0
    pages: set[int] = set()
    with pdfplumber.open(path) as doc:
        for index, page in enumerate(doc.pages, 1):
            for char in page.chars:
                left = max(0.0, -float(char["x0"]))
                right = max(0.0, float(char["x1"]) - page.width)
                top = max(0.0, -float(char["top"]))
                bottom = max(0.0, float(char["bottom"]) - page.height)
                if top > 0.1 or bottom > 0.1:
                    raise SystemExit(
                        f"vertical glyph overflow on translated page {index}: "
                        f"top={top:.2f}pt bottom={bottom:.2f}pt"
                    )
                if left > 0.1 or right > 0.1:
                    pages.add(index)
                    max_left = max(max_left, left)
                    max_right = max(max_right, right)
    return max_left, max_right, sorted(pages)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("translated", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--gutter", type=float, default=12.0)
    args = parser.parse_args()
    if args.gutter < 0:
        raise SystemExit("gutter must be non-negative")

    translated = PdfReader(str(args.translated))
    source = PdfReader(str(args.source))
    if len(translated.pages) != len(source.pages):
        raise SystemExit(
            f"page mismatch: translated={len(translated.pages)} source={len(source.pages)}"
        )

    overflow_left, overflow_right, overflow_pages = translated_overflow(args.translated)
    if overflow_pages:
        raise SystemExit(
            "translated glyph overflow: "
            f"pages={','.join(map(str, overflow_pages))} "
            f"left={overflow_left:.2f}pt right={overflow_right:.2f}pt; "
            "repair translation layout and regenerate the translated PDF"
        )

    writer = PdfWriter()
    for index, (jp_page, source_page) in enumerate(
        zip(translated.pages, source.pages), 1
    ):
        if jp_page.rotation % 360 or source_page.rotation % 360:
            raise SystemExit(f"rotated page unsupported at pair {index}; normalize rotation first")
        jp_left, jp_bottom, jp_width, jp_height = dimensions(jp_page)
        en_left, en_bottom, en_width, en_height = dimensions(source_page)
        canvas_height = max(jp_height, en_height)
        canvas_width = jp_width + args.gutter + en_width
        canvas = PageObject.create_blank_page(width=canvas_width, height=canvas_height)

        jp_y = (canvas_height - jp_height) / 2
        en_y = (canvas_height - en_height) / 2
        canvas.merge_transformed_page(
            jp_page,
            Transformation().translate(tx=-jp_left, ty=jp_y - jp_bottom),
            over=True,
        )
        canvas.merge_transformed_page(
            source_page,
            Transformation().translate(
                tx=jp_width + args.gutter - en_left,
                ty=en_y - en_bottom,
            ),
            over=True,
        )
        writer.add_page(canvas)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as stream:
        writer.write(stream)

    result = PdfReader(str(args.output))
    if len(result.pages) != len(source.pages):
        raise SystemExit("final page count mismatch")
    for index, (out_page, jp_page, source_page) in enumerate(
        zip(result.pages, translated.pages, source.pages), 1
    ):
        _, _, jp_width, jp_height = dimensions(jp_page)
        _, _, en_width, en_height = dimensions(source_page)
        _, _, out_width, out_height = dimensions(out_page)
        expected_width = jp_width + args.gutter + en_width
        expected_height = max(jp_height, en_height)
        if abs(out_width - expected_width) > 0.01 or abs(out_height - expected_height) > 0.01:
            raise SystemExit(f"canvas size mismatch at pair {index}")
    print(
        f"pages={len(result.pages)} pairs={len(source.pages)} "
        f"layout=Japanese-left/source-right gutter={args.gutter:g}pt "
        "translated_overflow=none"
    )


if __name__ == "__main__":
    main()
