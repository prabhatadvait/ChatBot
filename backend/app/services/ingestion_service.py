import io
import os
import uuid
from fastapi import UploadFile
from typing import List
from app.core.text_splitter import split_text_into_chunks
from app.core.embeddings import Embedder
from app.repository.qdrant_repo import QdrantRepository
import PyPDF2

# Instantiate embedder and repo (singleton-style)
EMBEDDER = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
QDRANT = QdrantRepository()

async def ingest_document(file: UploadFile) -> int:
    """
    Extract text from uploaded file (PDF or plain text), chunk it, embed chunks,
    and store in Qdrant. Returns number of inserted chunks.
    """
    content = await file.read()
    filename = file.filename or f"doc-{uuid.uuid4()}.txt"
    text = ""

    # PDF extraction
    if filename.lower().endswith(".pdf"):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")
    else:
        try:
            text = content.decode(errors="ignore")
        except Exception as e:
            raise RuntimeError(f"Failed to decode file: {e}")

    if not text.strip():
        raise RuntimeError("No text extracted from the uploaded document.")

    chunks = split_text_into_chunks(text)
    embeddings = EMBEDDER.embed_documents(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    # Upsert to qdrant
    QDRANT.upsert_documents(ids=ids, vectors=embeddings, payloads=[{"text": c, "source": filename} for c in chunks])
    return len(chunks)

async def ingest_audio_file(file: UploadFile) -> int:
    """
    Save uploaded audio to a temporary path and attempt transcription using
    any available local transcription tool (not included here). For now,
    this function raises NotImplementedError if transcription is not available.
    """
    # Save file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Placeholder: user should replace this block with a call to a local ASR (e.g., whisper)
    # For now, try to use whisper if installed.
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(temp_path)
        text = result.get("text", "")
    except Exception as e:
        # If transcription not available, inform caller; alternatively, you can fallback.
        raise RuntimeError(f"Transcription failed or whisper not installed: {e}")

    if not text.strip():
        raise RuntimeError("Transcription produced empty text.")

    chunks = split_text_into_chunks(text)
    embeddings = EMBEDDER.embed_documents(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    QDRANT.upsert_documents(ids=ids, vectors=embeddings, payloads=[{"text": c, "source": file.filename} for c in chunks])
    return len(chunks)