from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

from .config import Settings
from .models import GlossaryEntry
from .security import assert_local_url


class TranslationError(RuntimeError):
    pass


def build_prompt(glossary: list[GlossaryEntry]) -> str:
    terms = "\n".join(f"- {item.source} => {item.target}" for item in glossary)
    glossary_section = (
        f"\n次の用語集を必ず優先し、表記を統一してください。\n{terms}\n"
        if terms
        else ""
    )
    return f"""あなたは学術論文専門の翻訳エンジンです。
入力を${{lang_in}}から${{lang_out}}へ正確で自然な学術文体で翻訳してください。
数式プレースホルダー、引用番号、URL、DOI、単位、変数名、略語を変更しないでください。
説明、前置き、Markdownコードフェンスを加えず、翻訳結果だけを出力してください。
{glossary_section}
原文:
${{text}}

訳文だけを返してください。 /no_think
"""


def build_command(
    settings: Settings,
    source: Path,
    output_dir: Path,
    prompt_file: Path,
    model: str,
    source_language: str,
    target_language: str,
) -> list[str]:
    if not model or any(ch.isspace() for ch in model):
        raise ValueError("モデル名が不正です")
    assert_local_url(settings.ollama_host)
    return [
        settings.pdf2zh_bin,
        str(source),
        "-li",
        source_language,
        "-lo",
        target_language,
        "-s",
        "ollama",
        "-t",
        "1",
        "-o",
        str(output_dir),
        "--prompt",
        str(prompt_file),
    ]


def run_translation(
    settings: Settings,
    job_dir: Path,
    model: str,
    source_language: str,
    target_language: str,
    glossary: list[GlossaryEntry],
) -> tuple[Path, Path]:
    source = job_dir / "source.pdf"
    output_dir = job_dir / "engine-output"
    output_dir.mkdir(exist_ok=True)
    prompt_file = job_dir / "prompt.txt"
    prompt_file.write_text(build_prompt(glossary), encoding="utf-8")

    if shutil.which(settings.pdf2zh_bin) is None:
        raise TranslationError(
            "pdf2zh が見つかりません。先に ./scripts/setup.sh を実行してください。"
        )
    assert_local_url(settings.ollama_host)

    env = {
        **os.environ,
        "OLLAMA_HOST": settings.ollama_host,
        "OLLAMA_MODEL": model,
        "PYTHONPATH": os.pathsep.join(
            filter(
                None,
                [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH")],
            )
        ),
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "no_proxy": "127.0.0.1,localhost,::1",
    }
    command = build_command(
        settings,
        source,
        output_dir,
        prompt_file,
        model,
        source_language,
        target_language,
    )
    log_path = job_dir / "translator.log"
    with log_path.open("w", encoding="utf-8") as log:
        result = subprocess.run(
            command,
            cwd=job_dir,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-3000:]
        raise TranslationError(f"翻訳エンジンが終了コード {result.returncode} で停止しました。\n{tail}")

    mono = _find_output(output_dir, "mono")
    dual = _find_output(output_dir, "dual")
    translated = job_dir / "translated.pdf"
    bilingual = job_dir / "bilingual.pdf"
    shutil.copy2(mono, translated)
    shutil.copy2(dual, bilingual)
    return translated, bilingual


def inspect_page_counts(source: Path, translated: Path) -> tuple[int, int, bool]:
    source_pages = len(PdfReader(str(source)).pages)
    translated_pages = len(PdfReader(str(translated)).pages)
    return source_pages, translated_pages, source_pages == translated_pages


def _find_output(directory: Path, kind: str) -> Path:
    candidates = sorted(directory.rglob(f"*-{kind}.pdf"))
    if not candidates:
        candidates = sorted(directory.rglob(f"*{kind}*.pdf"))
    if not candidates:
        raise TranslationError(f"{kind} PDFが生成されませんでした")
    return candidates[0]
