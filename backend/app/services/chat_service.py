from typing import List, Dict, Any
from app.repository.qdrant_repo import QdrantRepository
from app.core.embeddings import Embedder
import os

QDRANT = QdrantRepository()
EMBEDDER = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"))

async def answer_query(query: str, conversation_id: str = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Embed the query, search Qdrant for top_k contexts, and build an answer.
    The current LLM call is a placeholder: the function synthesizes a simple answer
    by concatenating retrieved contexts. Replace call to 'synthesize_answer' with a
    proper LLM chain (LangChain + model) when ready.
    """
    import uuid
    
    # If no conversation_id, start a new one
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        is_new_conversation = True
    else:
        is_new_conversation = False

    try:
        query_vector = EMBEDDER.embed_query(query)
        print(f"DEBUG: Query vector len={len(query_vector)}")
        
        results = QDRANT.search(collection_name="documents", vector=query_vector, limit=top_k, with_payload=True)
        print(f"DEBUG: Search returned {len(results)} hits")
        
        contexts = [hit["payload"]["text"] for hit in results]
        
        # For now, synthesize a naive answer by returning the most relevant context plus an echo
        answer = synthesize_answer(query, contexts)
        
        # Upsert conversation metadata (title based on first query if new, or just update timestamp)
        # In a real app we might want to generate a summary title. For now use truncated query.
        if is_new_conversation:
            title = (query[:30] + '...') if len(query) > 30 else query
            QDRANT.upsert_conversation(conversation_id=conversation_id, title=title)
        
        # store chat
        QDRANT.upsert_chat(conversation_id=conversation_id, query=query, response=answer, vector=query_vector)
        
        return {
            "conversation_id": conversation_id,
            "answer": answer, 
            "retrieved_count": len(contexts), 
            "contexts": contexts
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in answer_query: {e}")
        # Return a polite error message instead of crashing
        return {"answer": f"I apologize, but I encountered an internal error: {str(e)}", "retrieved_count": 0, "contexts": []}

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

async def get_conversations():
    return QDRANT.get_conversations()

async def get_chat_history(conversation_id: str):
    return QDRANT.get_chat_history(conversation_id)

async def delete_chat(conversation_id: str):
    QDRANT.delete_chat(conversation_id)

# --- Folders ---
async def create_folder(name: str):
    import uuid
    folder_id = str(uuid.uuid4())
    QDRANT.upsert_folder(folder_id, name)
    return {"id": folder_id, "name": name}

async def get_folders():
    return QDRANT.get_folders()

async def delete_folder(folder_id: str):
    QDRANT.delete_folder(folder_id)

async def move_chat_to_folder(conversation_id: str, folder_id: str):
    # To "move", we update the conversation metadata.
    # Currently we don't have a "get_conversation_metadata" easily, 
    # but upsert_conversation overwrites/merges if we provide same ID.
    # However we need the Title. 
    # Hack: We just update it. Qdrant payload is replaced by default in upsert unless we fetch first.
    # Let's fetch conversations list to find the title first.
    conversations = await get_conversations()
    target = next((c for c in conversations if c["id"] == conversation_id), None)
    if target:
        QDRANT.upsert_conversation(conversation_id, title=target.get("title", "Chat"), folder_id=folder_id)