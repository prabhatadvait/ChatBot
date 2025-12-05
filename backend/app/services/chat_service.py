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
    results = QDRANT.search(collection_name="documents", vector=query_vector, limit=top_k, with_payload=True)
    contexts = [hit["payload"]["text"] for hit in results]
    # For now, synthesize a naive answer by returning the most relevant context plus an echo
    answer = synthesize_answer(query, contexts)
    # store chat
    QDRANT.upsert_chat(query=query, response=answer, vector=query_vector)
    return {"answer": answer, "retrieved_count": len(contexts), "contexts": contexts}

def synthesize_answer(query: str, contexts: List[str]) -> str:
    """
    Very simple synthesizer: include the top context and echo the user's question.
    Replace this with LLM call for production.
    """
    if not contexts:
        return "I could not find relevant information in the ingested documents."
    top_context = contexts[0]
    return f"Based on retrieved document context:\n\n{top_context}\n\nUser Question:\n{query}\n\n(Replace this placeholder with a real LLM for natural responses.)"

async def reset_chat_history():
    QDRANT.clear_chat_collection()