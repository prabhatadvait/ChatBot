import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer

# Connect to Qdrant (using internal container hostname)
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

print(f"--- Connecting to Qdrant at {url} ---")
client = QdrantClient(url=url)

# List collections
try:
    collections = client.get_collections()
    print(f"Collections: {[c.name for c in collections.collections]}")
except Exception as e:
    print(f"Error listing collections: {e}")

COLLECTION_NAME = "documents"

# Check Documents Collection
print(f"\n--- Checking Collection: {COLLECTION_NAME} ---")
try:
    info = client.get_collection(COLLECTION_NAME)
    print(f"Status: {info.status}")
    print(f"Vector Config: {info.config.params.vectors}")
    print(f"Points Count: {info.points_count}")
except Exception as e:
    print(f"Error getting collection info: {e}")

# Test Embedding & Search
print(f"\n--- Test Search ---")
try:
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Loading model: {model_name}...")
    model = SentenceTransformer(model_name)
    
    query_text = "test query"
    query_vector = model.encode(query_text).tolist()
    print(f"Generated vector length: {len(query_vector)}")

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=5,
        with_payload=True
    )
    print(f"Search Results ({len(results)} hits):")
    for hit in results:
        print(f" - Score: {hit.score}, Payload: {hit.payload}")
except Exception as e:
    print(f"Error during search test: {e}")
