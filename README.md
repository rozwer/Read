# Readable

Codexで英語の論文PDFを日本語に翻訳し、原文と見比べられる対訳PDFを作るためのリポジトリです。
翻訳・レビュー・PDF組版・検品の手順と、その実行に使うスクリプトをSkillとして同梱しています。

## 作成するPDF

各ページを **日本語が左・対応する原文が右** の見開きにして、次の2種類を作ります。

- **readable**：日本語の文字をやや小さくし、句読点を考慮して改行する版。
- **standard**：原文の文字サイズを基準に、通常の改行で組む版。

原文のページ対応、図表、数式、引用を保ち、翻訳後に意味のレビューとレイアウト検査を行います。
詳細な手順は [翻訳Skill](.agents/skills/readable-pdf-translation/SKILL.md)、エージェント向けの作業ルールは [AGENTS.md](AGENTS.md) を参照してください。

## 必要なもの

- macOSまたはLinux
- このフォルダで作業できるCodexの利用環境
- `uv` と Poppler（`pdftoppm`、`pdfinfo`）
- 翻訳する英語の論文PDF

Python 3.12、PDF検査用ライブラリ、PDFMathTranslate 1.9.11はセットアップスクリプトで導入します。
翻訳はCodexが行うため、ローカルLLMをダウンロードする必要はありません。

## 使い方

### 1. リポジトリを取得する

```bash
git clone https://github.com/rozwer/Readable.git
cd Readable
```

ZIPで取得した場合も、隠しフォルダの `.agents/` を含むフォルダ全体を利用してください。

### 2. 実行環境を準備する

macOSでHomebrewを使う場合は、次のコマンドで必要なツールを準備できます。
Linuxでは `uv` とPopplerを各環境の方法で導入してください。

```bash
brew install uv poppler
```

リポジトリのルートで、Skill用のセットアップを実行します。

```bash
bash scripts/setup.sh --skill
```

`pdf2zh` が見つからない場合は `uv tool update-shell` を実行し、ターミナルを開き直してください。
依存パッケージやレイアウト解析モデル、フォントの初回取得にはネットワーク接続が必要になる場合があります。

### 3. Codexで翻訳を依頼する

このフォルダをCodexで開き、PDFのパスを指定して依頼します。

```text
このリポジトリの .agents/skills/readable-pdf-translation/SKILL.md を使い、
/絶対パス/paper.pdf を日本語に翻訳してください。
作業データは data/jobs/paper/ に保存し、規定のレビューと目視検査を行って、
readable・standardの対訳PDFを作成してください。
```

同名Skillが個人環境にもある場合は、上記のようにリポジトリ内のパスを指定してください。
Skillの配置については [OpenAI公式ドキュメント](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills) を参照できます。

## 処理の流れと出力

1. PDFから翻訳対象を抽出し、前後の文脈と用語辞書を参照してCodexで翻訳します。
2. 初回翻訳とは別の工程で各訳文をレビューし、確認済みの訳文マップを作ります。
3. 訳文をPDFに組み込み、原文と並べた2種類の対訳PDFを生成します。
4. ページ対応、文字のはみ出し、実際の表示を検査します。

作業データは `data/jobs/<job-id>/`、最終PDFはその中の `output/` に保存します。
訳文マップ、レビュー監査、完了検証記録もジョブ内に残します。
翻訳対象のテキストはCodexに渡されます。

## リポジトリ構成

```text
AGENTS.md                               # エージェント向け作業ルール
.agents/skills/readable-pdf-translation/  # 翻訳・レビュー・組版・検証のSkill
scripts/setup.sh                        # 環境準備
pyproject.toml / uv.lock                 # Pythonの依存関係
data/jobs/                              # 論文ごとの作業データ（Git対象外）
docs/legacy-web-app.md                   # 旧Webアプリの利用手順
src/local_readable/                      # 旧Webアプリの実装
tests/                                  # Webアプリのテスト
```

論文PDF、翻訳結果、ログ、仮想環境、モデル、認証情報は共有対象に含めません。
Skillのスクリプトを個別に実行する場合は、リポジトリのルートから `uv run --locked --extra skill python .agents/skills/readable-pdf-translation/scripts/<script>.py ...` を使います。

旧Webアプリもソースとして残っています。
その起動手順とローカルモデルを使う方式の説明は [旧Webアプリのドキュメント](docs/legacy-web-app.md) にあります。

## 依存ソフトウェア

PDFの抽出・組版にはPDFMathTranslateを使用します。
PDFMathTranslateはAGPL-3.0です。
配布やサービス化の際は、依存先のライセンス条件を確認してください。
