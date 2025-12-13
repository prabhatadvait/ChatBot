from typing import List, Dict, Any
from app.repository.qdrant_repo import QdrantRepository
from app.core.embeddings import Embedder
import os

QDRANT = QdrantRepository()
EMBEDDER = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

async def answer_query(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Embed the query, search Qdrant for top_k contexts, and build an answer.
    The current LLM call is a placeholder: the function synthesizes a simple answer
    by concatenating retrieved contexts. Replace call to 'synthesize_answer' with a
    proper LLM chain (LangChain + model) when ready.
    """
    query_vector = EMBEDDER.embed_query(query)
    print(f"DEBUG: Query vector len={len(query_vector)}")
    results = QDRANT.search(collection_name="documents", vector=query_vector, limit=top_k, with_payload=True)
    print(f"DEBUG: Search returned {len(results)} hits")
    contexts = [hit["payload"]["text"] for hit in results]
    # For now, synthesize a naive answer by returning the most relevant context plus an echo
    answer = synthesize_answer(query, contexts)
    # store chat
    QDRANT.upsert_chat(query=query, response=answer, vector=query_vector)
    return {"answer": answer, "retrieved_count": len(contexts), "contexts": contexts}

from google import genai

def synthesize_answer(query: str, contexts: List[str]) -> str:
    """
    Synthesize an answer using Google Gemini API.
    """
    if not contexts:
        return "I could not find relevant information in the ingested documents."
    
    # Gemini 2.0 Flash has a large context window, so we can include more chunks if needed.
    # We'll stick to top 3-5 for now to keep it focused, but it can handle much more.
    context_blob = "\n\n".join(contexts[:5]) 
    
    prompt = f"""You are a helpful assistant. Use the following pieces of retrieved context to answer the question. 
If the answer is not in the context, say you don't know, but try to be helpful based on the context provided.

Context:
{context_blob}

Question: {query}
"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not set."
        
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return f"I encountered an error connecting to the intelligence engine: {e}"

async def reset_chat_history():
    QDRANT.clear_chat_collection()

async def get_chat_history():
    return QDRANT.get_recent_chats()