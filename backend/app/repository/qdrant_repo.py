import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from typing import List, Dict, Any

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

class QdrantRepository:
    def __init__(self):
        # connect to Qdrant; when running inside Docker, set QDRANT_HOST to 'qdrant'
        url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
        self.client = QdrantClient(url=url)
        self.doc_collection = "documents"
        self.doc_collection = "documents"
        self.chat_collection = "chats" # Stores individual messages
        self.conversation_collection = "conversations" # Stores conversation metadata
        self.folder_collection = "folders" # Stores folder metadata


        # ensure collections exist with a default vector size (will be recreated later once embedder available)
        # we will lazily create collections with correct vector size via set_collection_vector_size if needed

    def set_collection_vector_size(self, collection_name: str, vector_size: int):
        try:
            # delete and recreate to ensure correct size
            if self.client.get_collection(collection_name=collection_name):
                self.client.delete_collection(collection_name=collection_name)
        except Exception:
            pass
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
        )

    def upsert_documents(self, ids: List[str], vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        if not vectors:
            return
        # ensure collection vector size matches
        vector_size = len(vectors[0])
        try:
            info = self.client.get_collection(collection_name=self.doc_collection)
            if info.config.params.vectors.size != vector_size:
                 self.set_collection_vector_size(self.doc_collection, vector_size)
        except Exception:
            self.set_collection_vector_size(self.doc_collection, vector_size)
        points = [
            rest.PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i])
            for i in range(len(ids))
        ]
        try:
            self.client.upsert(collection_name=self.doc_collection, points=points)
            print(f"DEBUG: Upserted {len(points)} points to {self.doc_collection}")
        except Exception as e:
            print(f"DEBUG: Upsert failed: {e}")

    
    def _search_impl(self, collection_name: str, vector: List[float], limit: int, with_payload: bool):
        # Fallback logic for different qdrant-client versions
        if hasattr(self.client, "search"):
            return self.client.search(
                collection_name=collection_name, 
                query_vector=vector, 
                limit=limit, 
                with_payload=with_payload
            )
        elif hasattr(self.client, "search_points"):
             # Sometimes exposed as search_points in older/async variants
             return self.client.search_points(
                collection_name=collection_name, 
                vector=vector, 
                limit=limit, 
                with_payload=with_payload
             )
        else:
             # Fallback to recommended HTTP models direct usage or raw API if needed
             # But for now, let's assume one of the above works or we use query_points (v1.10+)
             return self.client.query_points(
                 collection_name=collection_name,
                 query=vector,
                 limit=limit,
                 with_payload=with_payload
             ).points

    def search(self, collection_name: str, vector: List[float], limit: int = 5, with_payload: bool = True):
        # Search and return list of dicts with payloads
        try:
            hits = self._search_impl(collection_name, vector, limit, with_payload)
            print(f"DEBUG: Search in {collection_name} returned {len(hits)} hits")
        except Exception as e:
            print(f"DEBUG: Search failed for collection {collection_name}: {e}")
            # If collection doesn't exist or other error, return empty
            return []
        results = []
        for hit in hits:
            payload = hit.payload if hasattr(hit, "payload") else (hit.payload or {})
            results.append({"id": hit.id, "score": hit.score, "payload": payload})
        return results

    def upsert_chat(self, conversation_id: str, query: str, response: str, vector: List[float]):
        # store chat as a point in chat_collection
        try:
            info = self.client.get_collection(collection_name=self.chat_collection)
            # Check if dimension matches
            if info.config.params.vectors.size != len(vector):
                self.set_collection_vector_size(self.chat_collection, len(vector))
        except Exception:
            self.set_collection_vector_size(self.chat_collection, len(vector))
        import uuid
        import time
        # We store the conversation_id in the payload so we can filter by it
        point = rest.PointStruct(
            id=str(uuid.uuid4()), 
            vector=vector, 
            payload={
                "conversation_id": conversation_id,
                "query": query, 
                "response": response,
                "timestamp": time.time()
            }
        )
        self.client.upsert(collection_name=self.chat_collection, points=[point])

    def upsert_conversation(self, conversation_id: str, title: str, folder_id: str = None):
        # We use a dummy vector for conversations as we just want to list them
        # Alternatively, we could just rely on distinct conversation_ids in chat_collection, 
        # but a separate collection is cleaner for listing "Recent Chats" without aggregation.
        try:
            self.client.get_collection(collection_name=self.conversation_collection)
        except Exception:
             # Create with size 1 dummy
             self.client.recreate_collection(
                 collection_name=self.conversation_collection,
                 vectors_config=rest.VectorParams(size=1, distance=rest.Distance.COSINE),
            )
            
        import time
        payload = {
            "title": title,
            "updated_at": time.time()
        }
        if folder_id:
            payload["folder_id"] = folder_id

        point = rest.PointStruct(
            id=conversation_id,
            vector=[0.0], # Dummy
            payload=payload
        )
        self.client.upsert(collection_name=self.conversation_collection, points=[point])

    def delete_chat(self, conversation_id: str):
        # Delete messages
        try:
            self.client.delete(
                collection_name=self.chat_collection,
                points_selector=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="conversation_id",
                            match=rest.MatchValue(value=conversation_id)
                        )
                    ]
                )
            )
        except Exception as e:
            print(f"Error deleting chat messages: {e}")

        # Delete conversation metadata
        try:
             self.client.delete(
                collection_name=self.conversation_collection,
                points_selector=rest.PointIdsList(points=[conversation_id])
            )
        except Exception as e:
            print(f"Error deleting conversation metadata: {e}")

    # --- Folder Management ---
    def upsert_folder(self, folder_id: str, name: str):
        try:
            self.client.get_collection(collection_name=self.folder_collection)
        except Exception:
             self.client.recreate_collection(
                 collection_name=self.folder_collection,
                 vectors_config=rest.VectorParams(size=1, distance=rest.Distance.COSINE),
            )
        import time
        point = rest.PointStruct(
            id=folder_id,
            vector=[0.0],
            payload={"name": name, "created_at": time.time()}
        )
        self.client.upsert(collection_name=self.folder_collection, points=[point])

    def delete_folder(self, folder_id: str):
        try:
            self.client.delete(
                collection_name=self.folder_collection,
                points_selector=rest.PointIdsList(points=[folder_id])
            )
            # Optionally: Un-link conversations in this folder? 
            # For simplicity, we won't strictly enforce referential integrity here unless requested.
            # But let's at least try to untag them if we were thorough. 
            # For now, just deleting the folder is enough; chats will just have a dead folder_id or we can handle it in UI.
        except Exception:
            pass
            
    def get_folders(self) -> List[Dict[str, Any]]:
        try:
            response, _ = self.client.scroll(
                collection_name=self.folder_collection,
                limit=100,
                with_payload=True
            )
            results = []
            for point in response:
                payload = point.payload or {}
                results.append({
                    "id": point.id,
                    "name": payload.get("name", "Unnamed"),
                    "created_at": payload.get("created_at", 0)
                })
            results.sort(key=lambda x: x["created_at"])
            return results
        except Exception:
            return []

    def clear_chat_collection(self):
        try:
            self.client.delete_collection(collection_name=self.chat_collection)
        except Exception:
            pass
        # recreate empty chat collection with fallback size 1 (will be set correctly on next upsert)
        try:
            self.client.recreate_collection(
                collection_name=self.chat_collection,
                vectors_config=rest.VectorParams(size=768, distance=rest.Distance.COSINE),
            )
        except Exception:
            pass
        
        try:
             self.client.delete_collection(collection_name=self.conversation_collection)
        except Exception:
            pass
        try:
            self.client.recreate_collection(
                 collection_name=self.conversation_collection,
                 vectors_config=rest.VectorParams(size=1, distance=rest.Distance.COSINE), # Dummy vector
            )
        except Exception:
             pass

    def get_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            response, _ = self.client.scroll(
                collection_name=self.conversation_collection,
                limit=limit,
                with_payload=True
            )
            # Sort by updated_at desc (client side sort if scroll doesn't support easy sort without creating payload index)
            # For now, simplistic retrieval
            results = []
            for point in response:
                payload = point.payload or {}
                results.append({
                    "id": point.id, # This is the conversation_id
                    "title": payload.get("title", "New Chat"),
                    "updated_at": payload.get("updated_at", 0),
                    "folder_id": payload.get("folder_id")
                })
            results.sort(key=lambda x: x["updated_at"], reverse=True)
            return results
        except Exception as e:
            # If collection missing, return empty
            return []

    def get_chat_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        try:
            # We need to filter by conversation_id. 
            # In Qdrant, we can use a Filter.
            scroll_filter = rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="conversation_id",
                        match=rest.MatchValue(value=conversation_id)
                    )
                ]
            )
            response, _ = self.client.scroll(
                collection_name=self.chat_collection,
                scroll_filter=scroll_filter,
                limit=100, # Max messages per chat for now
                with_payload=True
            )
            results = []
            for point in response:
               payload = point.payload or {}
               if payload.get("query") and payload.get("response"):
                   results.append({
                       "id": point.id,
                       "query": payload.get("query"),
                       "response": payload.get("response"),
                       "timestamp": payload.get("timestamp", 0)
                   })
            results.sort(key=lambda x: x["timestamp"])
            return results
        except Exception as e:
            print(f"Error fetching chat history: {e}")
            return []
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []