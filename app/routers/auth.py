"""Auth router — register (parent/tutor) + rate-limited login."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import TutorProfile, User
from app.schemas import LoginIn, RegisterIn, TokenOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


def _issue(user: User) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        name=user.full_name,
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()  # get user.id
    if payload.role == "tutor":
        # create an empty profile; tutor fills it in later
        db.add(
            TutorProfile(
                user_id=user.id,
                headline="",
                fee_per_hour=500,
                subjects=[],
                classes=[],
                areas=[],
            )
        )
    db.commit()
    return _issue(user)


@router.post("/login", response_model=TokenOut)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended. Contact support.")
    return _issue(user)
