from __future__ import annotations

import json
import threading
from pathlib import Path

from .models import JobRecord, utc_now


class JobStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def job_dir(self, job_id: str) -> Path:
        if not job_id or any(ch not in "0123456789abcdef" for ch in job_id):
            raise ValueError("不正なジョブIDです")
        return self.root / job_id

    def create(self, record: JobRecord) -> JobRecord:
        with self._lock:
            directory = self.job_dir(record.id)
            directory.mkdir(parents=False, exist_ok=False)
            self._write(record)
        return record

    def get(self, job_id: str) -> JobRecord:
        path = self.job_dir(job_id) / "job.json"
        if not path.exists():
            raise KeyError(job_id)
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, job_id: str, **changes: object) -> JobRecord:
        with self._lock:
            record = self.get(job_id)
            changes["updated_at"] = utc_now()
            updated = record.model_copy(update=changes)
            self._write(updated)
            return updated

    def list(self) -> list[JobRecord]:
        records: list[JobRecord] = []
        for path in self.root.glob("*/job.json"):
            try:
                records.append(JobRecord.model_validate_json(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
        return sorted(records, key=lambda item: item.created_at, reverse=True)

    def _write(self, record: JobRecord) -> None:
        path = self.job_dir(record.id) / "job.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(record.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

