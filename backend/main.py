from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, uuid, io
from typing import Optional
from qdrant_client import QdrantClient
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

app = FastAPI(title="Secure Self-Hosted Chatbot - Backend")

# CORS (Front-end Requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment setup
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Database client
qdrant = QdrantClient(url="qdrant", port=6333, prefer_grpc=False)

# Embeddings + Chunking
embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
TEXT_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
DOC_COLLECTION = "documents"
CHAT_COLLECTION = "chats"

def ensure_collections():
    # Create document collection
    try:
        qdrant.recreate_collection(
            collection_name=DOC_COLLECTION,
            vectors_config={"size": embedder.embedding_dimension, "distance": "Cosine"},
        )
    except Exception:
        pass
    # Create chat collection
    try:
        qdrant.recreate_collection(
            collection_name=CHAT_COLLECTION,
            vectors_config={"size": embedder.embedding_dimension, "distance": "Cosine"},
        )
    except Exception:
        pass

@app.on_event("startup")
async def startup_event():
    ensure_collections()

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

@app.post("/api/upload/document")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    text = ""

    # PDF extraction
    if file.filename.lower().endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        except Exception:
            raise HTTPException(status_code=400, detail="PDF extraction failed.")
    else:
        try:
            text = content.decode(errors="ignore")
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to decode file.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text extracted from the document.")

    chunks = TEXT_SPLITTER.split_text(text)
    vectors = [embedder.embed_documents([c])[0] for c in chunks]
    ids = [str(uuid.uuid4()) for _ in chunks]

    qdrant.upsert(
        collection_name=DOC_COLLECTION,
        points=[{"id": ids[i], "vector": vectors[i], "payload": {"text": chunks[i], "source": file.filename}} for i in range(len(chunks))]
    )

    return {"status": "ok", "inserted": len(chunks)}

@app.post("/api/upload/voice")
async def upload_voice(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(audio_bytes)

    # Attempt transcription
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(temp_path)
        text = result["text"]
    except Exception:
        raise HTTPException(status_code=500, detail="Whisper not installed or transcription failed.")

    if not text.strip():
        raise HTTPException(status_code=500, detail="Transcription resulted in empty text.")

    chunks = TEXT_SPLITTER.split_text(text)
    vectors = [embedder.embed_documents([c])[0] for c in chunks]
    ids = [str(uuid.uuid4()) for _ in chunks]

    qdrant.upsert(
        collection_name=DOC_COLLECTION,
        points=[{"id": ids[i], "vector": vectors[i], "payload": {"text": chunks[i], "source": file.filename}} for i in range(len(chunks))]
    )

    return {"status": "ok", "inserted": len(chunks)}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # Retrieve similar docs
    query_vector = embedder.embed_documents([req.query])[0]
    search = qdrant.search(
        collection_name=DOC_COLLECTION,
        query_vector=query_vector,
        limit=req.top_k,
        with_payload=True,
    )

    contexts = [hit.payload["text"] for hit in search]
    prompt = "Context:\n" + "\n---\n".join(contexts) + f"\n\nUser: {req.query}\nAssistant:"

    # Call LLM (placeholder)
    answer = call_llm(prompt)

    # Store in chat history
    chat_id = str(uuid.uuid4())
    qdrant.upsert(
        collection_name=CHAT_COLLECTION,
        points=[{
            "id": chat_id,
            "vector": query_vector,
            "payload": {"query": req.query, "response": answer}
        }]
    )

    return {"answer": answer, "retrieved_count": len(contexts)}

def call_llm(prompt: str) -> str:
    """
    IMPORTANT:
    This is a placeholder LLM that lets you test your entire RAG pipeline
    without needing an API key or paid model.
    You must replace this with a LangChain LLM wrapper later.
    """
    return "This is a placeholder LLM response. Replace call_llm() with a real LangChain LLM chain."

@app.post("/api/chat/reset")
async def reset_chat():
    try:
        qdrant.delete_collection(collection_name=CHAT_COLLECTION)
    except Exception:
        pass

    # Recreate empty chat collection
    try:
        qdrant.recreate_collection(
            collection_name=CHAT_COLLECTION,
            vectors_config={"size": embedder.embedding_dimension, "distance": "Cosine"},
        )
    except Exception:
        pass

    return {"status": "ok", "message": "Chat history cleared."}

@app.get("/")
def root():
    return {"message": "Backend running"}