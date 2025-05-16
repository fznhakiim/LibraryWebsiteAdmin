from utils.firestore_client import db

def create_user(username: str):
    doc_ref = db.collection('users').document()  # auto-generate ID
    doc_ref.set({'username': username})
    return doc_ref.id

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
