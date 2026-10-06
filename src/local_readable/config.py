from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    jobs_dir: Path
    static_dir: Path
    pdf2zh_bin: str = "pdf2zh"
    ollama_host: str = "http://127.0.0.1:11434"
    max_upload_bytes: int = 200 * 1024 * 1024

    @classmethod
    def discover(cls) -> "Settings":
        root = Path(__file__).resolve().parents[2]
        return cls(
            root=root,
            jobs_dir=root / "data" / "jobs",
            static_dir=root / "src" / "local_readable" / "static",
        )

