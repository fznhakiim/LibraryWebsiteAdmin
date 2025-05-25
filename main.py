from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routes import test_route, user_route, book_route
from google.cloud import firestore
import os
import shutil
import uuid
from dotenv import load_dotenv
from routes import admin_route
from routes import user_route



load_dotenv()  # baca file .env otomatis

# Set environment variable GOOGLE_APPLICATION_CREDENTIALS hanya jika belum ada
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    # bisa kasih fallback atau raise error jika perlu
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS not set in environment variables")

# sekarang os.environ sudah punya GOOGLE_APPLICATION_CREDENTIALS dari .env


# Inisialisasi Firestore client
db = firestore.Client()

app = FastAPI()

app.include_router(admin_route.router)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan asal frontend untuk keamanan
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder untuk akses gambar
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pastikan folder upload ada
UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Register routers
app.include_router(test_route.router, prefix="/test", tags=["test"])
app.include_router(user_route.router, prefix="/users", tags=["users"])
app.include_router(book_route.router, prefix="/books", tags=["books"])

@app.post("/books/")
async def create_book(title: str, author: str, stock: int, image: UploadFile = File(None)):
    image_url = None

    # Simpan gambar jika ada
    if image:
        ext = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_location = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_url = f"http://localhost:8000/static/images/{unique_filename}"

    # Simpan data ke Firestore
    book_data = {
        "title": title,
        "author": author,
        "stock": stock,
        "image_url": image_url
    }

    try:
        doc_ref = db.collection("books").document()
        doc_ref.set(book_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return JSONResponse(status_code=201, content={"message": "Book created", "data": book_data})
