# Local Readable

論文PDFを英日翻訳し、元ページとの対応を保ったまま閲覧・保存するツールです。Ollamaで翻訳するローカルWebアプリと、Codexで翻訳・レビューするSkillを同梱しています。

## 共有内容とCodex Skill

翻訳Skillは [`.agents/skills/readable-pdf-translation/SKILL.md`](.agents/skills/readable-pdf-translation/SKILL.md) にあります。翻訳・レビュー規則、プロンプト、抽出・組版・検証スクリプトを含みます。リポジトリを共有すると、このSkillも一緒に渡せます。

エージェント向けの作業ルールは [AGENTS.md](AGENTS.md) にまとめています。翻訳Skillの参照先、検証方法、作業データの扱い、指摘を受けた際の修正対応を定めています。

```text
AGENTS.md                               # エージェント向け作業ルール
.agents/skills/readable-pdf-translation/  # Codex翻訳ワークフロー一式
src/local_readable/                      # ローカルWebアプリ
scripts/                                # 起動・セットアップと従来の連携補助
tests/                                  # アプリのテスト
data/jobs/                              # 各自の論文・訳文・検証記録（共有対象外）
```

### 受け取った人の使い方（Codexで翻訳）

1. ZIPを展開、またはリポジトリをcloneし、フォルダ全体をCodexで開きます。隠しフォルダの `.agents/` も必要です。
2. `uv` と Poppler を用意します。macOSでHomebrewを使う場合は `brew install uv poppler` で導入できます。
3. リポジトリのルートで次を実行します。

   ```bash
   bash scripts/setup.sh --skill
   ```

   Python 3.12、SkillのPDF検査ライブラリ、PDFMathTranslate 1.9.11を準備します。この方式はOllama互換のローカルブリッジを使うため、Ollama本体やローカルLLMの取得は不要です。`pdf2zh` が見つからない場合は `uv tool update-shell` を実行し、ターミナルを開き直してください。

4. Codexで次のように依頼します。PDFは各自で用意してください。

   ```text
   このリポジトリの .agents/skills/readable-pdf-translation/SKILL.md を使い、
   /絶対パス/paper.pdf を日本語に翻訳してください。
   作業データは data/jobs/paper/ に保存し、規定のレビューと目視検査を行って、
   readable・standardの対訳PDFを作成してください。
   ```

Codexはプロジェクト内の `.agents/skills/` を読み込みます。同名Skillが個人環境にもある場合は上記のようにパスを指定してください。詳しくは [OpenAI公式のSkill配置説明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills) を参照してください。

Skill内のPythonスクリプトは、リポジトリのルートから `uv run --extra skill python .agents/skills/readable-pdf-translation/scripts/<script>.py ...` で実行します。翻訳手順の正本は同梱の `SKILL.md` です。外部の個人用Skillフォルダを参照する必要はありません。

Codex方式では翻訳対象のテキストをCodexに渡します。以下のローカル処理の説明は、Ollamaを使うWebアプリに適用されます。

### 共有するもの・各自で用意するもの

共有ZIPにはアプリ、Skill、テスト、依存関係定義、セットアップ手順を含めます。論文PDF、翻訳結果、ログ、仮想環境、モデル、認証情報は含めません。Gitで共有する場合も、`data/jobs/` の作業データなどは `.gitignore` で除外します。

受け取り側ではCodexの利用環境、上記の依存ツール、入力PDFが必要です。依存パッケージ・レイアウト解析モデル・フォントの初回取得にはネットワーク接続が必要になる場合があります。共有ZIPは `dist/` に置きます。

## Webアプリのローカル処理

- サーバーは `127.0.0.1` のみで待ち受けます。
- 翻訳先はローカルの Ollama (`127.0.0.1:11434`) に固定しています。
- PDF、訳文、用語辞書、ログは `data/jobs/` 以外へ送信しません。
- PDFMathTranslateの `ollama` サービス以外は呼び出しません。

## 必要なもの

- macOS または Linux
- Python 3.12（`uv` が自動で用意できます）
- Ollama
- Poppler (`pdftoppm`, `pdfinfo`)
- PDFMathTranslate (`pdf2zh`)

## セットアップ

```bash
./scripts/setup.sh
ollama pull qwen2.5:14b
./scripts/run.sh
```

ブラウザで <http://127.0.0.1:8765> を開きます。

モデルは日本語翻訳品質を優先するなら `qwen2.5:14b` 以上を推奨します。小さいMacでは `qwen2.5:7b` も使用できます。

## SPOKテスト

評価対象は次のオープンアクセス論文を想定しています。

> Fei Huang et al., “SPOK: tokenizing geographic space for enhanced spatial reasoning in GeoAI,” International Journal of Geographical Information Science 39(12), 2768–2808.

出版社の「View PDF」から保存し、任意で `fixtures/spok.pdf` に置いてください。現在の配布版は、出版社の表紙・書誌ページ1ページと論文本体41ページを合わせた全42ページ（約5.6 MB）です。

```bash
pdfinfo fixtures/spok.pdf | grep Pages
./scripts/smoke_spok.sh fixtures/spok.pdf
```

初回はレイアウト解析モデルの取得が発生する場合があります。取得後の翻訳処理はローカルのみです。

## Webアプリの出力

各ジョブは `data/jobs/<job-id>/` に保存されます。

- `source.pdf`: 原文
- `translated.pdf`: 原ページ構成を維持した訳文
- `bilingual.pdf`: 原文と訳文を交互に配置した対訳PDF
- `job.json`: 状態、設定、QA結果
- `translator.log`: ローカル処理ログ

Codex Skillでは、ジョブ内の `output/` に日本語が左・原文が右の `readable` / `standard` PDFを作ります。訳文マップ、意味レビュー監査、完了検証記録もジョブ内に保存します。

## ライセンス上の注意

PDFMathTranslateはAGPL-3.0です。本プロジェクトはローカル利用を前提にしています。配布やネットワークサービス化を行う場合は、依存先を含むライセンス条件を確認してください。
