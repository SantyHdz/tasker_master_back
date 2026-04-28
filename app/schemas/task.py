from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority_id: int
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority_id: Optional[int] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    priority_id: int
    due_date: Optional[datetime]
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True