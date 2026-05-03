# app/api/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.AI.vital_classifier.pipeline import process_user_query
from app.AI.vital_classifier import session_store

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: int
    message: str
    # Frontend can optionally send back its own context summary
    context_summary: Optional[dict] = None


class ClearRequest(BaseModel):
    user_id: int


@router.post("/chat")
def chat(req: ChatRequest):
    result = process_user_query(
        req.user_id,
        req.message,
        context_summary=req.context_summary
    )
    return {
        "reply": result["answer"],
        "vitals": result["vitals"],
        "buckets": result["buckets"],
        "summary": result["summary"],            # ← frontend persists this
        "cached_vitals_used": result["cached_vitals_used"],  # ← for debugging
    }


@router.post("/chat/clear")
def clear_chat(req: ClearRequest):
    session_store.clear_session(req.user_id)
    return {"status": "cleared"}