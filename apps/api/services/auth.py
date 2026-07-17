"""
Salkım AI — JWT Kimlik Doğrulama Servisi

Doküman 5.2: HTTPS + JWT (15 dk access + 30 gün refresh token)
Auth: Telefon numarası + şifre ile giriş (kullanıcı kararı)

Fallback Environment Variable Pattern:
  JWT_SECRET_KEY env'den okunur, yoksa dev fallback kullanılır.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.user import User

# --- Konfigürasyon ---
JWT_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "salkim_dev_insecure_secret_key_change_in_production_123456",
)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15        # Doküman 5.2: 15 dakika
REFRESH_TOKEN_EXPIRE_DAYS = 30          # Doküman 5.2: 30 gün

# --- Şifre Hash ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Bearer Token Scheme ---
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hash'ler."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Plain text şifreyi hash ile karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT access token oluşturur.

    Args:
        data: Token payload (sub: user_id)
        expires_delta: Özel süre (varsayılan 15 dk)

    Returns:
        JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT refresh token oluşturur (30 gün).

    Args:
        data: Token payload (sub: user_id)
        expires_delta: Özel süre (varsayılan 30 gün)

    Returns:
        JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT token'ı decode eder. Geçersiz/süresi dolmuş ise HTTPException fırlatır."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token süresi dolmuş.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token.",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI Depends — Bearer token'dan kullanıcıyı çözer.

    Kullanım:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            ...
    """
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token gerekli, refresh token kullanılamaz.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token'da kullanıcı bilgisi bulunamadı.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı.",
        )

    return user
