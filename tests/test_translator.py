from pathlib import Path

from local_readable.config import Settings
from local_readable.models import GlossaryEntry
from local_readable.translator import build_command, build_prompt


def settings(tmp_path: Path) -> Settings:
    return Settings(root=tmp_path, jobs_dir=tmp_path / "jobs", static_dir=tmp_path)


def test_prompt_contains_glossary_and_protected_content():
    prompt = build_prompt([GlossaryEntry(source="spatial token", target="空間トークン")])
    assert "spatial token => 空間トークン" in prompt
    assert "DOI" in prompt
    assert "${text}" in prompt


def test_command_is_pinned_to_local_ollama(tmp_path: Path):
    command = build_command(
        settings(tmp_path),
        tmp_path / "source.pdf",
        tmp_path / "out",
        tmp_path / "prompt.txt",
        "qwen2.5:14b",
        "en",
        "ja",
    )
    assert command[command.index("-s") + 1] == "ollama"
    # pdf2zh 1.9.11's BabelDOC CLI path parses --prompt twice and crashes.
    assert "--babeldoc" not in command
    assert not any("openai" in item.lower() for item in command)
