from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import test_route  # pastikan test_route sudah benar
from routes import user_route
from utils.firestore_client import db  
from routes import test_route, user_route, book_route
from fastapi.staticfiles import StaticFiles
import os
import base64
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from google.cloud import firestore
from utils.firestore_client import db
import os
import shutil
import uuid
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Setup CORS (pindahkan ke atas sebelum router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan ["http://localhost:8080"] jika ingin lebih aman
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router untuk API
app.include_router(test_route.router, prefix="/test", tags=["test"])
app.include_router(user_route.router, prefix="/users", tags=["users"])
app.include_router(book_route.router, prefix="/books", tags=["books"])

UPLOAD_DIR = "static/images"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/books/")
async def create_book(title: str, author: str, stock: int, image: UploadFile = File(None)):
    image_url = None
    if image:
        # simpan file ke folder static/images
        os.makedirs("static/images", exist_ok=True)
        file_location = f"static/images/{image.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"http://localhost:8000/{file_location}"
    
    # Simpan data buku ke Firestore / DB, termasuk image_url
    # misal:
    # book_data = {"title": title, "author": author, "stock": stock, "image_url": image_url}

    return {"title": title, "author": author, "stock": stock, "image_url": image_url}

app.mount("/static", StaticFiles(directory="static"), name="static")