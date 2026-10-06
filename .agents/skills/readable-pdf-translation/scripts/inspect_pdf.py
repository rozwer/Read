#!/usr/bin/env python3
"""Inspect and render PDFs on all supported platforms without Poppler."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--pages", help="Comma-separated 1-based page numbers; default: all")
    parser.add_argument("--dpi", type=int, default=120)
    args = parser.parse_args()
    if not 36 <= args.dpi <= 600:
        parser.error("--dpi must be between 36 and 600")

    with pymupdf.open(args.pdf) as doc:
        try:
            pages = list(dict.fromkeys(int(n) for n in args.pages.split(","))) if args.pages else list(range(1, len(doc) + 1))
        except ValueError:
            parser.error("--pages must contain comma-separated integers")
        if any(n < 1 or n > len(doc) for n in pages):
            parser.error(f"--pages must be in 1..{len(doc)}")
        if args.render_dir:
            args.render_dir.mkdir(parents=True, exist_ok=True)
        result = {"pages": len(doc), "selected": []}
        for n in pages:
            page = doc[n - 1]
            item = {"page": n, "width": page.rect.width, "height": page.rect.height}
            if args.render_dir:
                output = args.render_dir / f"page-{n:04d}.png"
                page.get_pixmap(dpi=args.dpi, alpha=False).save(output)
                item["image"] = str(output.absolute())
            result["selected"].append(item)
        # ASCII JSON also survives Windows console code pages; paths remain lossless.
        print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
