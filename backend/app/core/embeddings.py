import os
from typing import List
from google import genai
from google.genai import types

class Embedder:
    """
    Wrapper around Google Gemini Embedding API.
    Default model: 'gemini-embedding-001'.
    """

    def __init__(self, model_name: str = "gemini-embedding-001"):
        self.model_name = model_name
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)

    @property
    def embedding_dim(self) -> int:
        # gemini-embedding-001 has 768 dimensions
        return 768

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts -> returns list of vector lists.
        """
        # Batch embedding is supported by some clients, but basic usage:
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query -> returns a single vector list.
        """
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        # result.embeddings is a list of ContentEmbedding objects
        # accessing .values gives the float list
        return result.embeddings[0].values