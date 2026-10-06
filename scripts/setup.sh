#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"

mode="${1:-web}"
case "$mode" in
  web|--skill) ;;
  *) echo "Usage: bash scripts/setup.sh [--skill]"; exit 2 ;;
esac

command -v uv >/dev/null || { echo "uv が必要です: https://docs.astral.sh/uv/"; exit 1; }
if [[ "$mode" == "web" ]]; then
  command -v ollama >/dev/null || { echo "Ollama が必要です: https://ollama.com/"; exit 1; }
  command -v pdftoppm >/dev/null || { echo "Poppler が必要です: brew install poppler"; exit 1; }
fi

uv sync --locked --python 3.12 --extra dev --extra skill
# pdf2zh 1.9.11 imports an API removed in tencentcloud-sdk-python-tmt 3.1.
# Pin the last compatible SDK even though this app never enables Tencent.
uv tool install --force --python 3.12 \
  --with 'tencentcloud-sdk-python-tmt==3.0.1257' \
  'pdf2zh==1.9.11'

if [[ "$mode" == "--skill" ]]; then
  echo "セットアップ完了。このフォルダを Codex で開き、同梱の readable-pdf-translation Skill を使用してください。"
else
  echo "セットアップ完了。次に Ollama モデルを用意してください:"
  echo "  ollama pull qwen2.5:14b"
fi
