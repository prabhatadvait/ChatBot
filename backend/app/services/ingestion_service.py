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




import speech_recognition as sr

# Instantiate embedder and repo (singleton-style)
EMBEDDER = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"))
QDRANT = QdrantRepository()

async def ingest_document(file: UploadFile) -> int:
    """
    Extract text from uploaded file (PDF or plain text), chunk it, embed chunks,
    and store in Qdrant. Returns number of inserted chunks.
    """
    import shutil
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # Save uploaded file temporarily
    input_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        documents = []
        if file.filename.lower().endswith(".pdf"):
            loader = PyPDFLoader(input_path)
            documents = loader.load()
        else:
            # Fallback for text files
            loader = TextLoader(input_path)
            documents = loader.load()

        if not documents:
             raise RuntimeError("No content extracted from document.")

        # Combine content for simplified chunking or chunk normally
        # PyPDFLoader returns one document per page usually.
        # We can split these documents further or just use them.
        # Requirements said: "read, chunk, and embed".
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks_docs = text_splitter.split_documents(documents)
        chunks = [doc.page_content for doc in chunks_docs]
        
        if not chunks:
             raise RuntimeError("No text extracted from the uploaded document.")

        embeddings = EMBEDDER.embed_documents(chunks)
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Upsert to qdrant
        # Note: payloads can now include metadata like page number if we wanted, 
        # but sticking to simple text payload for now to match current schema.
        QDRANT.upsert_documents(ids=ids, vectors=embeddings, payloads=[{"text": c, "source": file.filename} for c in chunks])
        return len(chunks)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Document ingestion failed: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


async def transcribe_audio(file: UploadFile) -> str:
    """
    Transcribe audio file using Google Web Speech API (Online).
    Converts input audio to WAV using ffmpeg before processing.
    """
    
    # Save uploaded file temporarily
    input_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    wav_path = f"{input_path}.wav"
    
    try:
        with open(input_path, "wb") as f:
            f.write(await file.read())
        
        # Convert to WAV using ffmpeg (SpeechRecognition prefers WAV)
        command = [
            "ffmpeg", "-i", input_path,
            "-f", "wav", wav_path,
            "-y" # overwrite
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Process with SpeechRecognition
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # Use Google Web Speech API
            try:
                transcription = recognizer.recognize_google(audio_data)
                return transcription
            except sr.UnknownValueError:
                return "" # Return empty string if nothing understood
            except sr.RequestError as e:
                raise RuntimeError(f"Could not request results from Google Speech Recognition service; {e}")

    except subprocess.CalledProcessError:
        raise RuntimeError("FFmpeg conversion failed. Ensure ffmpeg is installed.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Transcription failed: {str(e)}")
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