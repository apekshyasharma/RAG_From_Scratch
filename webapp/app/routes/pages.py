from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uuid

router = APIRouter()

# Get the correct templates directory path
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    # For now: generate a session id per page load
    session_id = str(uuid.uuid4())
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "session_id": session_id}
    )
