from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion_service import ingest_document, ingest_audio_file

router = APIRouter()

@router.post("/document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or text). The ingestion service will extract text,
    chunk, embed and store into Qdrant.
    """
    try:
        inserted = await ingest_document(file)
        return {"status": "ok", "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice")
async def upload_voice(file: UploadFile = File(...)):
    """
    Upload an audio file. This will attempt server-side transcription (if available),
    then ingest the transcribed text like a document.
    """
    try:
        inserted = await ingest_audio_file(file)
        return {"status": "ok", "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
