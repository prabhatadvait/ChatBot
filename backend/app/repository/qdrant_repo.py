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
        self.chat_collection = "chats"
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

    def upsert_chat(self, query: str, response: str, vector: List[float]):
        # store chat as a point in chat_collection
        try:
            info = self.client.get_collection(collection_name=self.chat_collection)
            # Check if dimension matches
            if info.config.params.vectors.size != len(vector):
                self.set_collection_vector_size(self.chat_collection, len(vector))
        except Exception:
            self.set_collection_vector_size(self.chat_collection, len(vector))
        import uuid
        point = rest.PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"query": query, "response": response})
        self.client.upsert(collection_name=self.chat_collection, points=[point])

    def clear_chat_collection(self):
        try:
            self.client.delete_collection(collection_name=self.chat_collection)
        except Exception:
            pass
        # recreate empty chat collection with fallback size 1 (will be set correctly on next upsert)
        try:
            self.client.recreate_collection(
                collection_name=self.chat_collection,
                vectors_config=rest.VectorParams(size=384, distance=rest.Distance.COSINE),
            )
        except Exception:
            pass

    def get_recent_chats(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            # Scroll through points to get history
            response, _ = self.client.scroll(
                collection_name=self.chat_collection,
                limit=limit,
                with_payload=True
            )
            results = []
            for point in response:
               payload = point.payload or {}
               # Only include if both query and response exist
               if payload.get("query") and payload.get("response"):
                   results.append({
                       "id": point.id,
                       "query": payload.get("query"),
                       "response": payload.get("response")
                   })
            return results
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []