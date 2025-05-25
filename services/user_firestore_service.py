from utils.firestore_client import db
from google.cloud import firestore


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

def search_users(query: str):
    users_ref = db.collection("users")
    docs = users_ref.stream()

    result = []
    for doc in docs:
        data = doc.to_dict()
        if query.lower() in data.get("username", "").lower() or \
           query.lower() in data.get("email", "").lower() or \
           query.lower() in data.get("fullname", "").lower():
            user = data
            user["id"] = doc.id
            result.append(user)
    return result
