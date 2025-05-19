from utils.firestore_client import db
from pydantic import BaseModel
from typing import Optional

def get_user(user_id: str):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def get_all_users():
    users = db.collection('users').stream()
    return [{**u.to_dict(), 'id': u.id} for u in users]

def update_user(user_id: str, username: str):
    db.collection('users').document(user_id).update({'username': username})

def delete_user(user_id: str):
    db.collection('users').document(user_id).delete()

def create_book(data: dict):
    book_ref = db.collection('books').document()
    book_ref.set({
        "title": data["title"],
        "author": data["author"],
        "stock": data["stock"],
        "imageUrl": data.get("imageUrl", None)
    })
