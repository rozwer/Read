# Windowsでの使い方

Windows（x64）上のPowerShellからセットアップし、リポジトリを開いたCodexで翻訳します。
Bash・WSL・Ollama本体・PopplerはSkillの実行には不要です。

## セットアップ

1. GitHubの「Code → Download ZIP」で取得して展開するか、Gitでcloneします。
2. PowerShellで `winget install --id astral-sh.uv -e` を実行します。
3. PowerShellを開き直し、展開した `Readable` フォルダに移動します。
4. 次を実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Python 3.12、プロジェクトの依存ライブラリ、PDFMathTranslate 1.9.11を導入します。
セットアップが失敗した場合は、そのエラーを解消してから続けてください。
`uv` の導入方法は [公式ドキュメント](https://docs.astral.sh/uv/getting-started/installation/#winget) にあります。

## Codexへの依頼例

このフォルダをCodexで開き、実際のPDFパスを指定します。

```text
このリポジトリの .agents/skills/readable-pdf-translation/SKILL.md を使い、
C:\Users\your-name\Documents\paper.pdf を日本語に翻訳してください。
WindowsのPowerShell環境です。
作業データは data/jobs/paper/ に保存し、規定のレビューと目視検査を行って、
readable・standardの対訳PDFを作成してください。
```

翻訳対象のテキストはCodexに渡されます。
出力先は `data\jobs\paper\output\` です。

## PDFのページ数確認・画像化

リポジトリのルートで実行します。パスに空白がある場合は引用符で囲みます。

```powershell
uv run --locked --extra skill python -X utf8 .agents/skills/readable-pdf-translation/scripts/inspect_pdf.py "C:\Users\your-name\Documents\paper.pdf"
```

1ページ目を画像として書き出す場合は、次のように指定します。

```powershell
uv run --locked --extra skill python -X utf8 .agents/skills/readable-pdf-translation/scripts/inspect_pdf.py "C:\Users\your-name\Documents\paper.pdf" --render-dir "data/jobs/paper/previews" --pages 1 --dpi 120
```

`--pages` を省略すると全ページを書き出します。
検品用の画像であり、納品する対訳PDFはベクター形式のまま保持します。

## ブリッジと組版の補足

Skill内の `OLLAMA_HOST` はローカルブリッジの接続先です。翻訳用のローカルモデルを起動する設定ではありません。
PowerShellでは環境変数を次の形で指定します。

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11435"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

ブリッジは別のPowerShellウィンドウなどで起動し、処理終了後はそのウィンドウで `Ctrl+C` を押して停止します。
訳文やレビューのJSONはUTF-8で保存してください。PowerShellの `>` で作るとUTF-16になる場合があるため、SkillのPythonスクリプトかUTF-8対応のエディタを使います。

組版スクリプトは `uv tool dir` からPDFMathTranslateのPython環境を見つけるため、`pdf2zh.exe` をテキストとして読む処理や、ユーザー名を固定したパスには依存しません。
uv以外でPDFMathTranslateを導入した場合は、組版スクリプトに `--pdf2zh-python "C:\path\to\Scripts\python.exe"` を渡してください。指定位置は `--` より前です。

## 検証範囲

[Portabilityワークフロー](https://github.com/rozwer/Readable/actions/workflows/portability.yml)でWindowsとLinuxのテストを実行します。
WindowsではPowerShellセットアップとPDFMathTranslateの組版ラッパー起動も検査します。
日本語・空白を含むパス、対訳PDFの合成と画像化は合成データで確認します。
[初回のWindows検証](https://github.com/rozwer/Readable/actions/runs/37447441027)では、12テスト、PowerShellセットアップ、PDFMathTranslate 1.9.11の組版ラッパー起動が成功しました。
実際の論文を最後まで翻訳する検証や目視検品は、このCIには含みません。各翻訳ジョブで別途確認してください。
