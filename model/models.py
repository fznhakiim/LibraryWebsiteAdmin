from pydantic import BaseModel, EmailStr
from typing import Optional

class Book(BaseModel):
    title: str
    author: str
    stock: int
    imageUrl: Optional[str] = None  # base64 string, bukan bytes
    is_available: bool

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True
