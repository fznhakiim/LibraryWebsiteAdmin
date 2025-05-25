from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.firestore_client import db
from services.auth_service import verify_password, create_access_token
from auth.oauth2_scheme import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])
admin_router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login_admin(request: LoginRequest):
    admins_ref = db.collection("admins")
    query = admins_ref.where("username", "==", request.username).limit(1).stream()
    admin = next(query, None)

    if not admin:
        raise HTTPException(status_code=401, detail="Admin tidak ditemukan")

    admin_data = admin.to_dict()
    if not verify_password(request.password, admin_data["password"]):
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token({"sub": request.username, "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/dashboard")
def admin_dashboard(admin: dict = Depends(get_current_admin)):
    return {"message": f"Selamat datang Admin {admin['sub']}"}

@admin_router.get("/admin/verify")
def verify_admin(payload=Depends(get_current_admin)):
    return {"message": "Token valid"}