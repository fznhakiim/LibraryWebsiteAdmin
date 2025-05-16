from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import test_route  # pastikan test_route sudah benar
from routes import user_route
from utils.firestore_client import db  
from routes import test_route, user_route, book_route

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
