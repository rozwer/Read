"""Process-local compatibility hooks for the PDF translation worker.

This module is imported automatically by Python when ``src`` is on
``PYTHONPATH``.  It only affects the pdf2zh subprocess created by Local
Readable.
"""

from __future__ import annotations

try:
    import ollama
except ImportError:
    ollama = None


if ollama is not None and not getattr(ollama.Client.chat, "_local_readable_no_think", False):
    _original_chat = ollama.Client.chat

    def _chat_without_thinking(self, *args, **kwargs):
        kwargs["think"] = False
        return _original_chat(self, *args, **kwargs)

    _chat_without_thinking._local_readable_no_think = True
    ollama.Client.chat = _chat_without_thinking
