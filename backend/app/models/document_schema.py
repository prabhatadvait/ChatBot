from pydantic import BaseModel
from typing import Optional

class DocumentInsertResult(BaseModel):
    status: str
    inserted: int
    source: Optional[str] = None
