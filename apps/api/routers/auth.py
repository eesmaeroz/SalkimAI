"""
Salkım AI — Auth Router'ı

Doküman 2.4:
  POST /api/v1/auth/register  → Kullanıcı kaydı
  POST /api/v1/auth/token     → JWT access + refresh token al
  POST /api/v1/auth/refresh   → Refresh token ile yeni access token
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.user import User
from apps.api.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter(tags=["auth"])


# --- Pydantic Şemaları ---

class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20, examples=["5551234567"])
    name: str = Field(..., min_length=2, max_length=100, examples=["Ahmet Yılmaz"])
    password: str = Field(..., min_length=6, max_length=128)


class RegisterResponse(BaseModel):
    message: str
    user_id: str


class TokenRequest(BaseModel):
    phone: str = Field(..., examples=["5551234567"])
    password: str = Field(..., examples=["mypassword123"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 dakika (saniye)


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


# --- Endpoint'ler ---

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Kullanıcı Kaydı",
)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Yeni kullanıcı kaydı oluşturur.
    Telefon numarası benzersiz olmalıdır.
    """
    # Telefon numarası kontrolü
    existing_user = db.query(User).filter(User.phone == request.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu telefon numarası zaten kayıtlı.",
        )

    # Kullanıcı oluştur
    new_user = User(
        phone=request.phone,
        name=request.name,
        hashed_password=hash_password(request.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RegisterResponse(
        message="Kullanıcı başarıyla oluşturuldu.",
        user_id=str(new_user.id),
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="JWT Token Al",
)
def login_for_token(request: TokenRequest, db: Session = Depends(get_db)):
    """
    Telefon numarası ve şifre ile JWT access + refresh token alır.
    Doküman 5.2: 15 dk access + 30 gün refresh token.
    """
    user = db.query(User).filter(User.phone == request.phone).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon numarası veya şifre hatalı.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Token Yenileme",
)
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh token kullanarak yeni bir access token alır.
    Refresh token'ın tipi 'refresh' olmalıdır.
    """
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçerli bir refresh token gerekli.",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı.",
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Kullanıcı Hesabını ve Verilerini Sil (KVKK)",
)
def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mevcut kullanıcının hesabını ve ilişkili tüm verilerini (seralar, tahminler vs.) kalıcı olarak siler.
    KVKK/GDPR "unutulma hakkı" gereksinimi.
    """
    db.delete(current_user)
    db.commit()
    return None
