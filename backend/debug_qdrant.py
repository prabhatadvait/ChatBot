import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# Add parent dir to path to import app modules
sys.path.append(os.path.join(os.getcwd(), '..'))
# If running from backend dir directly
sys.path.append(os.getcwd())

from app.core.embeddings import Embedder

# Connect to Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
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
    # Use the new Embedder class which relies on Gemini
    embedder = Embedder() 
    print(f"Loading model: {embedder.model_name}...")
    
    query_text = "test query"
    query_vector = embedder.embed_query(query_text)
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
