from fastapi import APIRouter, HTTPException
from utils.firestore_client import db
from datetime import datetime, timezone, timedelta
import logging
from fastapi import Body
from schemas.user_schemas import UserStatusUpdate
logger = logging.getLogger(__name__)

router = APIRouter()

# Manual translate nama bulan Indonesia
indonesian_months = {
    "January": "Januari", "February": "Februari", "March": "Maret",
    "April": "April", "May": "Mei", "June": "Juni",
    "July": "Juli", "August": "Agustus", "September": "September",
    "October": "Oktober", "November": "November", "December": "Desember"
}

def format_created_at(created_at):
    try:
        # Jika sudah datetime, langsung dipakai
        if isinstance(created_at, datetime):
            dt = created_at
        # Jika integer timestamp
        elif isinstance(created_at, int):
            dt = datetime.fromtimestamp(created_at)
        # Jika string ISO
        elif isinstance(created_at, str):
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            return str(created_at)  # fallback

        # Konversi ke WIB
        dt_local = dt.astimezone(timezone(timedelta(hours=7)))
        formatted = dt_local.strftime("%d %B %Y, %H:%M WIB")
        for en, idn in indonesian_months.items():
            formatted = formatted.replace(en, idn)
        return formatted
    except Exception as e:
        logger.error(f"Error format waktu: {e}")
        return str(created_at)


@router.get("/by-username/{username}")
async def get_user_by_username(username: str):
    users_ref = db.collection("users")
    query = users_ref.where("username", "==", username).limit(1).stream()

    for doc in query:
        data = doc.to_dict()

        if "createdAt" in data:
            data["createdAt"] = format_created_at(data["createdAt"])

        return data

    raise HTTPException(status_code=404, detail="User not found")

@router.get("/{user_id}")
async def get_user(user_id: str):
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        if "createdAt" in data:
            data["createdAt"] = format_created_at(data["createdAt"])
        data["id"] = doc.id
        return data
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/")
async def get_all_users():
    users_ref = db.collection("users")
    docs = users_ref.stream()
    users = []
    for doc in docs:
        data = doc.to_dict()
        if "createdAt" in data:
            data["createdAt"] = format_created_at(data["createdAt"])
        data["id"] = doc.id
        users.append(data)
    return users

@router.get("/detail/{user_id}")
async def get_user_with_borrowed_books(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_doc.to_dict()
    if "createdAt" in user_data:
        user_data["createdAt"] = format_created_at(user_data["createdAt"])
    user_data["id"] = user_doc.id

    # Ambil borrowed_books subcollection
    borrowed_books_ref = user_ref.collection("borrowed_books")
    borrowed_docs = borrowed_books_ref.stream()

    borrowed_books = []
    for bdoc in borrowed_docs:
        bdata = bdoc.to_dict()
        # format borrowDate jika perlu, contoh:
        if "borrowDate" in bdata:
            try:
                dt = datetime.fromisoformat(bdata["borrowDate"].replace("Z", "+00:00"))
                dt_local = dt.astimezone(timezone(timedelta(hours=7)))
                bdata["borrowDate"] = dt_local.strftime("%d %B %Y, %H:%M WIB")
            except:
                pass
        borrowed_books.append(bdata)
    
    user_data["borrowed_books"] = borrowed_books
    return user_data

@router.put("/status/{user_id}")
async def update_user_status(user_id: str, status_update: UserStatusUpdate):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User tidak ditemukan.")

    try:
        user_ref.update({"is_active": status_update.is_active})
        return {"detail": f"Status user diperbarui menjadi {'aktif' if status_update.is_active else 'nonaktif'}."}
    except Exception as e:
        logger.error(f"Gagal memperbarui status user: {e}")
        raise HTTPException(status_code=500, detail="Gagal memperbarui status user.")

