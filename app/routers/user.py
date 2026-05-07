from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TelegramLinkRequest
from app.utils.deps import get_current_user
from app.utils.security import hash_password, verify_n8n_api_key
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/telegram/link", status_code=200)
def link_telegram_account(
    telegram_data: TelegramLinkRequest,
    x_api_key: Optional[str] = Header(None, description="API key for n8n authentication"),
    db: Session = Depends(get_db)
):
    # Verify API key
    if not x_api_key or not verify_n8n_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Find user by email (not username - using email as identifier)
    user = db.query(User).filter(User.email == telegram_data.telegram_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. They must register in the app first")

    # Check if telegram_chat_id already linked to another user
    existing_link = db.query(User).filter(
        User.telegram_chat_id == telegram_data.telegram_chat_id,
        User.id != user.id
    ).first()
    if existing_link:
        raise HTTPException(status_code=409, detail="Telegram account already linked to another user")

    # Update telegram_chat_id
    user.telegram_chat_id = telegram_data.telegram_chat_id
    db.commit()
    db.refresh(user)

    return {
        "message": "Telegram linked successfully",
        "user_id": user.id,
        "telegram_chat_id": user.telegram_chat_id
    }