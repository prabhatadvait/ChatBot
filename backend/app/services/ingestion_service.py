import io
import os
import uuid
import json
import subprocess
from fastapi import UploadFile
from typing import List
from app.core.text_splitter import split_text_into_chunks
from app.core.embeddings import Embedder
from app.repository.qdrant_repo import QdrantRepository
import PyPDF2

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    Model = None
    KaldiRecognizer = None

# Instantiate embedder and repo (singleton-style)
EMBEDDER = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"))
QDRANT = QdrantRepository()

# Load Vosk model
VOSK_MODEL_PATH = "/app/model"
VOSK_MODEL = None

try:
    if os.path.exists(VOSK_MODEL_PATH):
        print(f"Loading Vosk model from {VOSK_MODEL_PATH}...")
        VOSK_MODEL = Model(VOSK_MODEL_PATH)
        print("Vosk model loaded.")
    else:
        print(f"WARNING: Vosk model not found at {VOSK_MODEL_PATH}. Transcription will fail.")
except Exception as e:
    print(f"Failed to load Vosk model: {e}")

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
    Transcribe audio file using offline Vosk model.
    Converts input audio to 16kHz mono WAV using ffmpeg before processing.
    """
    if VOSK_MODEL is None:
        raise RuntimeError("Vosk model is not loaded. Please ensure model is downloaded to /app/model.")

    # Save uploaded file temporarily
    input_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    wav_path = f"{input_path}.wav"
    
    try:
        with open(input_path, "wb") as f:
            f.write(await file.read())
        
        # Convert to 16kHz mono WAV using ffmpeg
        # -ac 1: mono, -ar 16000: 16kHz sample rate
        command = [
            "ffmpeg", "-i", input_path,
            "-ac", "1", "-ar", "16000",
            "-f", "wav", wav_path,
            "-y" # overwrite
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Process with Vosk
        rec = KaldiRecognizer(VOSK_MODEL, 16000)
        rec.SetWords(True) # Optional: enable word timestamps if needed, but we just want text
        
        transcription = ""
        
        with open(wav_path, "rb") as wf:
            while True:
                data = wf.read(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    # rec.Result() returns a json string with 'text'
                    res = json.loads(rec.Result())
                    transcription += res.get("text", "") + " "
        
        # Get final bits
        res = json.loads(rec.FinalResult())
        transcription += res.get("text", "")
        
        return transcription.strip()
        
    except subprocess.CalledProcessError:
        raise RuntimeError("FFmpeg conversion failed. Ensure ffmpeg is installed.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Vosk Transcription failed: {e}")
    finally:
        # Cleanup temp files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

async def ingest_audio_file(file: UploadFile) -> int:
    """
    Save uploaded audio to a temporary path and transcribe.
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