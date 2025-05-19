from pydantic import BaseModel
from typing import Optional

class Book(BaseModel):
    title: str
    author: str
    stock: int
    imageUrl: Optional[str] = None  # base64 string, bukan bytes
