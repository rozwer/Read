#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def content_digest(page) -> bytes:
    contents = page.get_contents()
    return hashlib.sha256(contents.get_data() if contents else b"").digest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("translated", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    translated = PdfReader(str(args.translated))
    source = PdfReader(str(args.source))
    if len(translated.pages) != len(source.pages):
        raise SystemExit(
            f"page mismatch: translated={len(translated.pages)} source={len(source.pages)}"
        )

    writer = PdfWriter()
    for translated_page, source_page in zip(translated.pages, source.pages):
        writer.add_page(translated_page)
        writer.add_page(source_page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as stream:
        writer.write(stream)

    result = PdfReader(str(args.output))
    if len(result.pages) != 2 * len(source.pages):
        raise SystemExit("final page count mismatch")
    for index, source_page in enumerate(source.pages):
        copied = result.pages[2 * index + 1]
        if copied.mediabox != source_page.mediabox:
            raise SystemExit(f"source MediaBox mismatch on page {index + 1}")
        if content_digest(copied) != content_digest(source_page):
            raise SystemExit(f"source content mismatch on page {index + 1}")
    print(f"pages={len(result.pages)} pairs={len(source.pages)} order=Japanese->source")


if __name__ == "__main__":
    main()
