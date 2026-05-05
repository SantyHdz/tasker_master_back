from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from app.routers import health
from app.routers import user as user_router
from app.routers import auth as auth_router
from app.routers import task as task_router
from app.models import user as user_model
from app.models import task as task_model
from app.models import priority as priority_model

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Tasker Master API",
    version="1.0.0",
    description="Task management API with user authentication and notification tracking"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS - adjust origins for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS:
    # Default to localhost for development
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(task_router.router)

@app.get("/")
def root():
    return {
        "message": "Tasker Master API running",
        "version": "1.0.0",
        "docs": "/docs"
    }