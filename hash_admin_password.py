import os
from google.cloud import firestore
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pastikan GOOGLE_APPLICATION_CREDENTIALS sudah diset
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS not set.")

# Inisialisasi Firestore
db = firestore.Client()

# Konfigurasi hashing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def update_admin_passwords():
    admins_ref = db.collection("admins")
    docs = admins_ref.stream()

    updated = 0
    skipped = 0

    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id

        # Skip jika password sudah di-hash (anggap sudah dalam bcrypt format jika diawali $2b$ atau $2a$)
        if "password" not in data or data["password"].startswith("$2"):
            skipped += 1
            continue

        hashed = hash_password(data["password"])
        admins_ref.document(doc_id).update({"password": hashed})
        print(f"Password admin {doc_id} berhasil di-hash.")
        updated += 1

    print(f"\nSelesai! {updated} admin diupdate, {skipped} dilewati karena sudah di-hash.")

if __name__ == "__main__":
    update_admin_passwords()
