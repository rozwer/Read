# Readable

このリポジトリは、Codexで論文を翻訳・レビューし、対訳PDFを作るSkillを共有します。セットアップと使い方は [README.md](README.md) を参照してください。旧ローカルWebアプリの実装も残っており、その手順は [docs/legacy-web-app.md](docs/legacy-web-app.md) にあります。

## 翻訳作業

- 論文PDFの翻訳には、リポジトリ同梱の [.agents/skills/readable-pdf-translation/SKILL.md](.agents/skills/readable-pdf-translation/SKILL.md) を読み、その手順に従ってください。個人環境にある同名Skillや絶対パスに依存しないでください。
- 翻訳・レビュー・組版・完了検証の詳細はSkillを正本とします。翻訳規則とレビュー規則はSkill内の `references/`、実行スクリプトはSkill内の `scripts/` にあります。
- 論文ごとの原文、用語辞書、訳文、監査記録、出力PDFは `data/jobs/<job-id>/` に保存してください。
- 既定の納品物は、日本語が左・原文が右の `readable` / `standard` 対訳PDFです。Skillで定めた意味レビュー、目視検査、完了検証を終えるまで納品完了と扱わず、報告には出力先と未確認事項を記載してください。

## 実装と検証

- Webアプリは `src/local_readable/`、そのテストは `tests/` にあります。Webアプリのローカル接続制限を維持してください。Codex方式では翻訳対象のテキストをCodexに渡すため、完全ローカル処理と説明しないでください。
- 依存関係は `pyproject.toml` と `uv.lock` で管理します。PDFMathTranslateは `scripts/setup.sh` で1.9.11に固定しており、Skillの組版ラッパーがこの実装に依存します。
- 環境準備は `bash scripts/setup.sh --skill`、アプリのテストは `uv run --locked --extra dev --extra skill pytest -q` です。SkillのPythonスクリプトは `uv run --locked --extra skill python .agents/skills/readable-pdf-translation/scripts/<script>.py ...` で実行できます。
- 変更内容に応じて検証してください。翻訳・組版の変更はPDFを生成して表示も確認し、単体テストの成功だけで翻訳品質やレイアウトの合格を主張しないでください。
- 論文PDF、訳文、ログ、認証情報、仮想環境、モデルはGitに追加しないでください。共有用コード・Skillと各論文の作業データは分けて管理します。

## Follow through on corrections

When the user points out a mistake, unmet requirement, or problem in ongoing work, treat it as a request to fix the work. Inspect the relevant state, make the correction, and verify the result before replying. Do not stop after acknowledging the issue, apologizing, or saying that you will fix it. Continue the original task after the correction until its requested outcome is complete.

If the user explicitly asks only for an explanation, asks you to stop, or says the next step needs their input or approval, follow that direction. If you cannot make the correction, state the concrete blocker and what work you completed.
