from fastapi import APIRouter,UploadFile,File,HTTPException
from app.services.ingestion_service import ingest_document, ingest_audio_files

router = APIRouter()

@router.post("/document")
async def upload_document(file: UploadFile=File(...)):
    """upload documet and ingestion service will extract text, chunk, embed and store into Qdrant."""