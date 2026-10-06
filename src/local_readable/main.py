from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .models import GlossaryEntry, JobRecord
from .security import assert_local_url
from .store import JobStore
from .translator import TranslationError, inspect_page_counts, run_translation


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.discover()
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    store = JobStore(settings.jobs_dir)
    app = FastAPI(title="Local Readable", docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.state.store = store

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        client = request.client.host if request.client else ""
        if client not in {"127.0.0.1", "::1", "localhost", "testclient"}:
            return JSONResponse({"detail": "ローカル接続のみ許可されています"}, status_code=403)
        return await call_next(request)

    @app.get("/api/status")
    def status() -> dict[str, object]:
        return {
            "localOnly": True,
            "ollamaHost": settings.ollama_host,
            "ollama": _ollama_models(settings.ollama_host),
        }

    @app.get("/api/jobs", response_model=list[JobRecord])
    def list_jobs() -> list[JobRecord]:
        return store.list()

    @app.get("/api/jobs/{job_id}", response_model=JobRecord)
    def get_job(job_id: str) -> JobRecord:
        try:
            return store.get(job_id)
        except (KeyError, ValueError):
            raise HTTPException(404, "ジョブが見つかりません") from None

    @app.post("/api/jobs", response_model=JobRecord, status_code=202)
    async def create_job(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        model: str = Form(...),
        glossary: str = Form("[]"),
        source_language: str = Form("en"),
        target_language: str = Form("ja"),
    ) -> JobRecord:
        if source_language != "en" or target_language != "ja":
            raise HTTPException(400, "現在は英語から日本語のみ対応しています")
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "PDFファイルを選択してください")
        try:
            parsed_glossary = [GlossaryEntry.model_validate(item) for item in json.loads(glossary)]
        except (json.JSONDecodeError, ValueError, TypeError):
            raise HTTPException(400, "用語辞書の形式が不正です") from None

        content = await file.read(settings.max_upload_bytes + 1)
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(413, "PDFは200MB以下にしてください")
        if not content.startswith(b"%PDF-"):
            raise HTTPException(400, "有効なPDFではありません")

        job_id = uuid.uuid4().hex
        record = JobRecord(
            id=job_id,
            filename=Path(file.filename).name,
            model=model,
            glossary=parsed_glossary,
            source_url=f"/api/jobs/{job_id}/files/source",
        )
        store.create(record)
        (store.job_dir(job_id) / "source.pdf").write_bytes(content)
        background_tasks.add_task(_process_job, settings, store, job_id)
        return record

    @app.get("/api/jobs/{job_id}/files/{kind}")
    def get_file(job_id: str, kind: str):
        names = {
            "source": "source.pdf",
            "translated": "translated.pdf",
            "bilingual": "bilingual.pdf",
        }
        if kind not in names:
            raise HTTPException(404, "ファイルが見つかりません")
        try:
            record = store.get(job_id)
            path = store.job_dir(job_id) / names[kind]
        except (KeyError, ValueError):
            raise HTTPException(404, "ジョブが見つかりません") from None
        if not path.exists():
            raise HTTPException(404, "ファイルはまだ生成されていません")
        download_name = f"{Path(record.filename).stem}-{kind}.pdf"
        return FileResponse(path, media_type="application/pdf", filename=download_name)

    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="static")
    return app


def _process_job(settings: Settings, store: JobStore, job_id: str) -> None:
    try:
        record = store.update(job_id, state="running", progress=10, message="PDFを解析しています")
        translated, _bilingual = run_translation(
            settings,
            store.job_dir(job_id),
            record.model,
            record.source_language,
            record.target_language,
            record.glossary,
        )
        store.update(job_id, progress=90, message="ページ対応を検査しています")
        source_pages, translated_pages, matches = inspect_page_counts(
            store.job_dir(job_id) / "source.pdf", translated
        )
        store.update(
            job_id,
            state="completed",
            progress=100,
            message="翻訳が完了しました" if matches else "翻訳完了（ページ数を確認してください）",
            source_pages=source_pages,
            translated_pages=translated_pages,
            page_count_matches=matches,
            translated_url=f"/api/jobs/{job_id}/files/translated",
            bilingual_url=f"/api/jobs/{job_id}/files/bilingual",
        )
    except Exception as exc:
        message = str(exc) if isinstance(exc, TranslationError) else f"処理に失敗しました: {exc}"
        store.update(job_id, state="failed", message="翻訳に失敗しました", error=message)


def _ollama_models(host: str) -> dict[str, object]:
    try:
        assert_local_url(host)
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2) as response:
            payload = json.load(response)
        return {"available": True, "models": [item["name"] for item in payload.get("models", [])]}
    except (OSError, ValueError, urllib.error.URLError, KeyError):
        return {"available": False, "models": []}


def run() -> None:
    uvicorn.run(create_app(), host="127.0.0.1", port=8765, access_log=False)


app = create_app()
