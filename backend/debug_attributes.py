import qdrant_client
from qdrant_client import QdrantClient
import inspect

print(f"Qdrant Client Version: {qdrant_client.__version__}")

try:
    client = QdrantClient(location=":memory:")
    print("Methods available on client:")
    methods = [m for m in dir(client) if not m.startswith("_")]
    print(methods)
    
    if hasattr(client, 'search'):
        print("YES, search exists.")
    else:
        print("NO, search does NOT exist.")
except Exception as e:
    print(f"Error inspecting client: {e}")
