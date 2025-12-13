import io
import os
import uuid
from fastapi import UploadFile
from typing import List
from app.core.text_splitter import split_text_into_chunks
from app.core.embeddings import Embedder
from app.repository.qdrant_repo import QdrantRepository
import PyPDF2
from google import genai

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

async def transcribe_audio(file: UploadFile) -> str:
    """
    Transcribe audio file using Google Gemini API.
    """
    # Save file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")

    try:
        client = genai.Client(api_key=api_key)
        
        # Upload file to Gemini
        myfile = client.files.upload(file=temp_path)
        
        # Wait for file to be active
        import time
        start_time = time.time()
        while myfile.state.name == "PROCESSING":
            if time.time() - start_time > 60:
                 raise RuntimeError("Timeout waiting for Gemini file processing.")
            
            time.sleep(2)
            try:
                myfile = client.files.get(name=myfile.name)
            except Exception as e:
                # transient error, just wait and try again
                print(f"DEBUG: Transient error polling file state: {e}")
                pass
            
        if myfile.state.name == "FAILED":
             raise RuntimeError(f"Google Gemini File Processing Failed: {myfile.error.message}")
        
        # Generate transcription
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=["Transcribe this audio clip verbatim.", myfile]
        )
        return response.text
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Gemini Audio Transcription Error: {e}")
        raise RuntimeError(f"Gemini Transcription failed: {e}")
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

async def ingest_audio_file(file: UploadFile) -> int:
    """
    Save uploaded audio to a temporary path and transcribe using Google Gemini API.
    Then chunk and ingest the text.
    """
    text = await transcribe_audio(file)

    if not text.strip():
        raise RuntimeError("Transcription produced empty text.")

    chunks = split_text_into_chunks(text)
    embeddings = EMBEDDER.embed_documents(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    QDRANT.upsert_documents(ids=ids, vectors=embeddings, payloads=[{"text": c, "source": file.filename} for c in chunks])
    return len(chunks)