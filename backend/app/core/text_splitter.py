from typing import List

def split_text_into_chunks(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
    """
    Simple character-based text splitter.
    Splits long text into overlapping chunks to be embedded.
    """
    text = text.replace("\r", "\n")
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks