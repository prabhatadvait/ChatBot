from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    answer: str
    retrieved_count: int
    contexts: List[str]