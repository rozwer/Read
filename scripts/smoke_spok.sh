#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 /path/to/spok.pdf" >&2
  exit 2
fi

source_pdf="$1"
test -f "$source_pdf" || { echo "PDFが見つかりません: $source_pdf" >&2; exit 1; }
pages="$(pdfinfo "$source_pdf" | awk '/^Pages:/ {print $2}')"
size="$(wc -c < "$source_pdf" | tr -d ' ')"
echo "SPOK fixture: ${pages} pages, ${size} bytes"
if [ "$pages" != "42" ]; then
  echo "警告: 想定したSPOK配布版は42ページ（出版社表紙1ページ＋論文本体41ページ）です" >&2
fi
echo "http://127.0.0.1:8765 からこのPDFを投入してください。"
