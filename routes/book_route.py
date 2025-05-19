from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from utils.firestore_client import db
from datetime import datetime, timezone, timedelta
import base64
import os
from model import Book

router = APIRouter()

# Helper untuk format tanggal (sama seperti kamu punya)
indonesian_months = {
    "January": "Januari", "February": "Februari", "March": "Maret",
    "April": "April", "May": "Mei", "June": "Juni",
    "July": "Juli", "August": "Agustus", "September": "September",
    "October": "Oktober", "November": "November", "December": "Desember"
}

def format_created_at(created_at_str: str):
    try:
        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        dt_local = dt.astimezone(timezone(timedelta(hours=7)))
        formatted = dt_local.strftime("%d %B %Y, %H:%M WIB")
        for en, idn in indonesian_months.items():
            formatted = formatted.replace(en, idn)
        return formatted
    except:
        return created_at_str

@router.get("/", tags=["books"])
async def get_books():
    books_ref = db.collection("books")
    docs = books_ref.stream()
    books = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if "createdAt" in data:
            data["createdAt"] = format_created_at(data["createdAt"])
        books.append(data)
    return books

@router.post("/", tags=["books"])
async def create_book(
    title: str = Form(...),
    author: str = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(None)
):
    book_data = {
        "title": title,
        "author": author,
        "stock": stock,
        "createdAt": datetime.utcnow().isoformat(),
    }
    
    if image:
        # Simpan file gambar ke folder static/images
        os.makedirs("static/images", exist_ok=True)
        file_path = f"static/images/{image.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        # Simpan URL file ke book_data
        book_data["imageUrl"] = f"http://localhost:8000/{file_path}"
    
    doc_ref = db.collection("books").add(book_data)
    return {"id": doc_ref[1].id}

@router.put("/{book_id}", tags=["books"])
async def update_book(book_id: str, book: dict):
    doc_ref = db.collection("books").document(book_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Book not found")
    doc_ref.update(book)
    return {"message": "Book updated"}

@router.delete("/{book_id}", tags=["books"])
async def delete_book(book_id: str):
    doc_ref = db.collection("books").document(book_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Book not found")
    doc_ref.delete()
    return {"message": "Book deleted"}
