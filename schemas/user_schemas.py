from pydantic import BaseModel
from typing import Optional

# Skema untuk membaca data (response)
class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True  # agar bisa bekerja dengan SQLAlchemy model


# Skema untuk membuat user (request)
class UserCreate(BaseModel):
    username: str

class UserUpdate(BaseModel):
    username: str

class UserStatusUpdate(BaseModel):
    is_active: bool

