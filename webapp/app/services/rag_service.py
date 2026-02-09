from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import Request


def _sse(event: str, data: dict) -> bytes:
    """
    Format SSE event payload as bytes:
      event: <event>\n
      data: <json>\n\n
    """
    payload = f"event: {event}\n" + f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return payload.encode("utf-8")


def _chunk_text_words(text: str, words_per_chunk: int = 1):
    """
    Stream output like tokens (word-by-word).
    words_per_chunk=1 => true "word-by-word" feel.
    """
    if not text:
        return
    words = text.split(" ")
    buf = []
    for w in words:
        buf.append(w)
        if len(buf) >= words_per_chunk:
            yield " ".join(buf) + " "
            buf = []
    if buf:
        yield " ".join(buf)


async def stream_rag_sse(
    rag,
    query: str,
    mode: str,
    request: Request,
    delay_s: float = 0.01,
) -> AsyncGenerator[bytes, None]:
    """
    Streams a RAG answer over SSE.

    Current version:
    - calls rag.answer(...) once (non-stream LLM)
    - then streams the final text word-by-word ("token" events)

    Later upgrade:
    - if LLM supports true streaming, replace the fallback chunking
      with actual token streaming from the model.
    """
    try:
        # If client disconnects early, stop work ASAP
        if await request.is_disconnected():
            return

        # (1) Run full RAG once
        result = rag.answer(query=query, mode=mode)
        text = result.answer or ""

        # (2) Stream "token" chunks (word-by-word)
        for piece in _chunk_text_words(text, words_per_chunk=1):
            if await request.is_disconnected():
                return
            yield _sse("token", {"text": piece})
            await asyncio.sleep(delay_s)

        # (3) Done
        yield _sse("done", {"ok": True, "mode_used": result.mode_used})

    except Exception as e:
        yield _sse("error", {"message": str(e)})
