import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class Embedder:
    """
    Wrapper around Google Gemini Embedding API using LangChain.
    Default model: 'models/embedding-001' (LangChain expects 'models/' prefix often, or just 'embedding-001').
    """

    def __init__(self, model_name: str = "models/embedding-001"):
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.embeddings = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=api_key)

    @property
    def embedding_dim(self) -> int:
        # gemini-embedding-001 has 768 dimensions
        return 768

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts -> returns list of vector lists.
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query -> returns a single vector list.
        """
        return self.embeddings.embed_query(text)