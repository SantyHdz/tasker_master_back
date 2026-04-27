from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority_id: int
    due_date: datetime | None = None

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    priority_id: int
    due_date: datetime | None
    is_completed: bool
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}