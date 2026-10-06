from fastapi.testclient import TestClient

from local_readable.config import Settings
from local_readable.main import create_app


def test_status_is_local_only(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("ok", encoding="utf-8")
    app = create_app(
        Settings(
            root=tmp_path,
            jobs_dir=tmp_path / "jobs",
            static_dir=static,
            ollama_host="http://127.0.0.1:9",
        )
    )
    with TestClient(app) as client:
        response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["localOnly"] is True


def test_rejects_non_pdf_upload(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("ok", encoding="utf-8")
    app = create_app(Settings(root=tmp_path, jobs_dir=tmp_path / "jobs", static_dir=static))
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs",
            files={"file": ("paper.pdf", b"not a pdf", "application/pdf")},
            data={"model": "qwen3:8b"},
        )
    assert response.status_code == 400

