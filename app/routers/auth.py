from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserCreate
from app.utils.security import verify_password, create_access_token, hash_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        400: {"description": "Bad Request - Invalid input or email already registered"},
        401: {"description": "Unauthorized - Invalid credentials"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    status_code=201,
    response_model=dict,
    summary="Register new user",
    description="Create a new user account with email and password. Returns JWT access token for immediate authentication.",
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        }
    }
)
@limiter.limit("5/minute")  # Limit to 5 registrations per minute
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    request: Request = None  # Required for rate limiting
):
    """
    Register a new user account.

    - **email**: User's email address (must be unique)
    - **password**: User's password (minimum 8 characters)
    - **name**: Optional display name

    Returns JWT access token for immediate authentication.
    """
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        name=user.name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post(
    "/login",
    response_model=dict,
    summary="User login",
    description="Authenticate user with email and password. Returns JWT access token.",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        }
    }
)
@limiter.limit("10/minute")  # Limit to 10 login attempts per minute
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None  # Required for rate limiting
):
    """
    Authenticate user and return JWT access token.

    - **email**: User's registered email address
    - **password**: User's password

    Returns JWT access token valid for 60 minutes.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}