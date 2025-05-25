from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

SECRET_KEY = "..."   # harus sama dengan create_access_token
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login", auto_error=False)

def get_current_admin(token: str = Depends(oauth2_scheme)):
    if token is None:
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Bukan admin")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    
    

