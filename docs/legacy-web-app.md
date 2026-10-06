# 旧ローカルWebアプリ

`src/local_readable/` には、Ollamaのローカルモデルで翻訳するWebアプリが残っています。
この文書はそのアプリを利用・保守するための手順です。
Codexによる翻訳Skillの使い方は [README](../README.md) を参照してください。

## 準備と起動

macOSまたはLinuxで、`uv`、Poppler、Ollamaを用意します。
Ollamaを起動し、使用する翻訳モデルをあらかじめ取得してください。
リポジトリのルートで次を実行します。

```bash
bash scripts/setup.sh web
bash scripts/run.sh
```

ブラウザで <http://127.0.0.1:8765> を開き、モデルを選択してPDFをアップロードします。
用語辞書の入力、進捗表示、原文と訳文の並列表示に対応しています。

## 処理と保存

サーバーは `127.0.0.1:8765` で待ち受け、PDFMathTranslateを介して `127.0.0.1:11434` のOllamaに翻訳を依頼します。
初回は依存パッケージやレイアウト解析モデルなどの取得が発生する場合があります。

ジョブごとに `data/jobs/<job-id>/` へ次のファイルを保存します。

- `source.pdf`：原文
- `translated.pdf`：訳文
- `bilingual.pdf`：原文と訳文を交互に配置したPDF
- `job.json`：状態、設定、ページ数の検査結果
- `translator.log`：処理ログ

このWebアプリは、Skillが定める独立した意味レビューや目視検査を自動実行しません。
Webアプリ上の完了表示は、Skillの納品条件を満たしたことを示すものではありません。

## 検証

```bash
uv run --locked --extra dev --extra skill pytest -q
```

SPOK論文のPDFを手元に用意した場合は、`bash scripts/smoke_spok.sh /絶対パス/spok.pdf` でページ数を確認できます。
このスクリプトは翻訳や品質評価を実行せず、Web画面からの投入を案内します。
