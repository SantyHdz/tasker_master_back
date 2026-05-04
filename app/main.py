from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health
from app.routers import user as user_router
from app.routers import auth as auth_router
from app.routers import task as task_router
from app.models import user as user_model
from app.models import task as task_model
from app.models import priority as priority_model

app = FastAPI(
    title="Tasker Master API",
    version="1.0.0",
    description="Task management API with user authentication and notification tracking"
)

# Configure CORS - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_methods=["*"],
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