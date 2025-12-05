import os
from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    """
    Wrapper around sentence-transformers SentenceTransformer.
    Default model: 'all-MiniLM-L6-v2' (small, fast, good performance).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @property
    def embedding_dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts -> returns list of vector lists.
        """
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query -> returns a single vector list.
        """
        vec = self.model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        return vec[0].tolist()