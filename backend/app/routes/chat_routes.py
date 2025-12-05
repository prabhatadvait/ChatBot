from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.chat_service import answer_query, reset_chat_history

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

@router.post("/query")
async def chat_query(req: ChatRequest):
    """
    Accepts a user query, retrieves top-k contexts, and returns an answer.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must be non-empty.")
    try:
        response = await answer_query(req.query, top_k=req.top_k)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset():
    """
    Reset chat history (clears chat collection).
    """
    try:
        await reset_chat_history()
        return {"status": "ok", "message": "chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
