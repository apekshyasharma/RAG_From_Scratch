# webapp/app/routes/api_chat.py
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "auto"  # fixed | semantic | both | auto

class ChatResponse(BaseModel):
    session_id: str
    mode_used: str
    answer: str

@router.post("/message", response_model=ChatResponse)
async def message(req: ChatRequest, request: Request):
    # RAG pipeline loaded on startup and stored in app.state
    rag = request.app.state.rag_pipeline

    # Call your pipeline (non-stream)
    result = rag.answer(query=req.message, mode=req.mode)

    return ChatResponse(
        session_id=req.session_id,
        mode_used=result.mode_used,
        answer=result.answer,
    )
