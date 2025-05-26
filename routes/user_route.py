from fastapi import APIRouter, HTTPException, Query, Request, Depends
from utils.firestore_client import db
from datetime import datetime, timezone, timedelta
import logging
from model import UserCreate
from fastapi import Body
from schemas.user_schemas import UserStatusUpdate
from fastapi import Query
from services.user_firestore_service import search_users, get_all_users
from typing import Optional
from firebase_admin import auth, credentials
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
    
async def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # contains 'uid', 'email', etc.
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

@router.get("/search")
def search_user(q: str = Query(None, description="Keyword pencarian user")):
    if not q:  # Jika query kosong, kembalikan semua user
        users_ref = db.collection("users")
        docs = users_ref.stream()
        users = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            users.append(data)
        return users

    users = search_users(q)
    if not users:
        return []
    return users


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
    """
    Get a user by ID along with their borrowed books and each borrowed book's full book details.
    """
    try:
        # Get the user document
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_data["id"] = user_doc.id

        # Format user's createdAt if present
        if "createdAt" in user_data:
            user_data["createdAt"] = format_created_at(user_data["createdAt"])

        # Get borrowed_books subcollection
        borrowed_books_ref = user_ref.collection("borrowed_books")
        borrowed_docs = borrowed_books_ref.stream()

        borrowed_books = []
        for bdoc in borrowed_docs:
            bdata = bdoc.to_dict()
            bdata["id"] = bdoc.id

            # Format borrowDate if present
            if "borrowDate" in bdata:
                try:
                    dt = datetime.fromisoformat(bdata["borrowDate"].replace("Z", "+00:00"))
                    dt_local = dt.astimezone(timezone(timedelta(hours=7)))
                    bdata["borrowDate"] = dt_local.strftime("%d %B %Y, %H:%M WIB")
                except:
                    pass

            # Fetch the actual book data
            book_id = bdata.get("bookId")
            if book_id:
                book_ref = db.collection("books").document(book_id)
                book_doc = book_ref.get()
                if book_doc.exists:
                    book_data = book_doc.to_dict()
                    book_data["id"] = book_doc.id

                    # Format createdAt of book if present
                    if "createdAt" in book_data:
                        book_data["createdAt"] = format_created_at(book_data["createdAt"])

                    bdata["book"] = book_data
                else:
                    bdata["book"] = None
            else:
                bdata["book"] = None

            borrowed_books.append(bdata)

        user_data["borrowed_books"] = borrowed_books

        return user_data

    except Exception as e:
        logger.error(f"Failed to retrieve user with borrowed books: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user with borrowed books")

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
    
@router.post("/", status_code=201)
async def create_user(
    user_data: UserCreate,
    token_data: dict = Depends(verify_firebase_token)):
    """
    Creates a new user in Firestore using Firebase UID as document ID
    Requires Firebase authentication
    """
    try:
        # Get UID from verified Firebase token
        uid = token_data['uid']

        # Prepare user data
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "phone": user_data.phone,
            "is_active": user_data.is_active,
            "createdAt": datetime.utcnow().isoformat(),
        }

        # Create document with UID as document ID
        user_ref = db.collection("users").document(uid)
        await user_ref.set(user_dict)

        # Format the created timestamp
        user_dict["id"] = uid
        user_dict["createdAt"] = format_created_at(user_dict["createdAt"])

        return user_dict

    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to create user"
        )

@router.post("/{user_id}/borrow", status_code=201)
async def borrow_book(
    user_id: str,
    book_id: str = Body(..., embed=True),
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Adds a book to user's borrowed_books subcollection.
    Requires Firebase authentication.
    
    Parameters:
    - user_id: ID of the user borrowing the book
    - book_id: ID of the book being borrowed
    """
    try:
        # Optional: Check if token_data['uid'] matches user_id
        # if token_data['uid'] != user_id:
        #     raise HTTPException(status_code=403, detail="Unauthorized")

        # Check if user exists
        user_ref = db.collection("users").document(user_id)
        if not user_ref.get().exists:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if book exists
        book_ref = db.collection("books").document(book_id)
        book_doc = book_ref.get()
        if not book_doc.exists:
            raise HTTPException(status_code=404, detail="Book not found")
        
        book_data = book_doc.to_dict()
        book_data["id"] = book_doc.id  # Include book ID in data
        borrowed_title = book_data["title"]

        # Create borrowed book record (embed the full book data)
        borrow_data = {
            "bookId": book_id,
            "bookTitle": borrowed_title,
            "borrowDate": datetime.utcnow().isoformat(),
            "status": "borrowed",
            "book": book_data
        }

        # Add to borrowed_books subcollection
        borrowed_books_ref = user_ref.collection("borrowed_books")
        new_borrow_ref = borrowed_books_ref.document()  # Auto-generated ID
        await new_borrow_ref.set(borrow_data)

        # Format the borrow date for response
        borrow_data["borrowDate"] = format_created_at(borrow_data["borrowDate"])
        borrow_data["id"] = new_borrow_ref.id

        return borrow_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to borrow book: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process book borrowing"
        )
    
@router.post("/{user_id}/borrowed_books/{borrowed_book_id}/return")
async def return_borrowed_book(
    user_id: str,
    borrowed_book_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Marks a borrowed book as returned.
    """
    try:
        # Validate user
        user_ref = db.collection("users").document(user_id)
        if not user_ref.get().exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate borrowed book record
        borrowed_book_ref = user_ref.collection("borrowed_books").document(borrowed_book_id)
        borrowed_doc = borrowed_book_ref.get()
        if not borrowed_doc.exists:
            raise HTTPException(status_code=404, detail="Borrowed book not found")
        
        # Update status to 'returned' and add returnDate
        borrowed_book_ref.update({
            "status": "returned",
            "returnDate": datetime.utcnow().isoformat()
        })

        return {"message": "Book marked as returned successfully!"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to return borrowed book: {e}")
        raise HTTPException(status_code=500, detail="Failed to process return")