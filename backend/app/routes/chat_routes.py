from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.services.chat_service import answer_query, reset_chat_history

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    top_k: Optional[int] = 5

@router.post("/")
async def chat_query(req: ChatRequest):
    """
    Accepts a user query, retrieves top-k contexts, and returns an answer.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must be non-empty.")
    try:
        response = await answer_query(req.query, conversation_id=req.conversation_id, top_k=req.top_k)
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

@router.get("/history")
async def get_history():
    """
    Retrieve recent conversations.
    """
    try:
        from app.services.chat_service import get_conversations
        conversations = await get_conversations()
        return {"history": conversations} # Keep key 'history' or change to 'conversations'? keeping 'history' for minimal breakage or consistency
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}")
async def get_chat_messages(conversation_id: str):
    """
    Retrieve messages for a specific conversation.
    """
    try:
        from app.services.chat_service import get_chat_history
        messages = await get_chat_history(conversation_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a specific conversation.
    """
    try:
        from app.services.chat_service import delete_chat
        await delete_chat(conversation_id)
        return {"status": "ok", "message": "conversation deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Folders ---
class FolderRequest(BaseModel):
    name: str

@router.get("/folders")
async def get_all_folders():
    try:
        from app.services.chat_service import get_folders
        folders = await get_folders()
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/folders")
async def create_new_folder(req: FolderRequest):
    try:
        from app.services.chat_service import create_folder
        folder = await create_folder(req.name)
        return folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/folders/{folder_id}")
async def remove_folder(folder_id: str):
    try:
        from app.services.chat_service import delete_folder
        await delete_folder(folder_id)
        return {"status": "ok"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def chat_transcribe(file: UploadFile = File(...)):
    """
    Transcribe audio file and return the text (for voice chat).
    """

    try:
        from app.services.ingestion_service import transcribe_audio
        text = await transcribe_audio(file)
        # We explicitly return it in a format the frontend can easily consume.
        # But for 'chat as query', returning pure text or {text: ...} is best.
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
