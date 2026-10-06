#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


START = "<<<SOURCE>>>"
END = "<<<END_SOURCE>>>"


class Store:
    def __init__(self, mode: str, path: Path):
        self.mode = mode
        self.path = path
        self.lock = threading.Lock()
        self.sources: dict[str, str] = {}
        self.translations: dict[str, str] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data.get("segments", []):
                self.sources[item["source"]] = item["id"]
            for item in data.get("translations", []):
                self.translations[item["source"]] = item["text"]

    def answer(self, source: str) -> str:
        with self.lock:
            if self.mode == "record":
                if source not in self.sources:
                    self.sources[source] = f"s{len(self.sources) + 1:05d}"
                    payload = {
                        "segments": [
                            {"id": segment_id, "source": text}
                            for text, segment_id in self.sources.items()
                        ]
                    }
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    self.path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                return source
            if source not in self.translations:
                raise KeyError(source)
            return self.translations[source]


def handler_for(store: Store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/api/tags":
                self._json(200, {"models": [{"name": "codex-bridge"}]})
            elif self.path == "/api/version":
                self._json(200, {"version": "0.1.0"})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                self._json(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            content = data.get("messages", [{}])[-1].get("content", "")
            match = re.search(re.escape(START) + r"(.*?)" + re.escape(END), content, re.DOTALL)
            if not match:
                self._json(400, {"error": "source markers missing"})
                return
            source = match.group(1)
            try:
                answer = store.answer(source)
            except KeyError:
                self._json(422, {"error": "translation missing", "source": source})
                return
            self._json(
                200,
                {
                    "model": data.get("model", "codex-bridge"),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "message": {"role": "assistant", "content": answer},
                    "done": True,
                },
            )

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("record", "serve"))
    parser.add_argument("data", type=Path)
    parser.add_argument("--port", type=int, default=11435)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(Store(args.mode, args.data)))
    print(f"codex translation bridge: mode={args.mode} http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
