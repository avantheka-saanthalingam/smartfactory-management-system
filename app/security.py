import os
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

# Set JWT_SECRET through the local environment or deployment secret manager for stable production sessions.
SECRET_KEY = os.getenv("JWT_SECRET") or os.urandom(32).hex()
ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()
oauth = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(value: str) -> str:
    return password_hash.hash(value)

def verify_password(value: str, encoded: str) -> bool:
    try:
        return password_hash.verify(value, encoded)
    except Exception:
        return False

def create_token(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "role": user.role.name, "exp": datetime.now(timezone.utc) + timedelta(hours=10)}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth), db: Session = Depends(get_db)) -> User:
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(User, int(payload.get("sub", "0")))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise invalid
    if not user or not user.active:
        raise invalid
    return user

def allow_roles(*roles: str):
    def guard(user: User = Depends(current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(status_code=403, detail="Your role cannot perform this action")
        return user
    return guard
