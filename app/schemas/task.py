from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority_id: int
    due_date: Optional[datetime] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure due_date is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority_id: Optional[int] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure due_date is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError("due_date must be timezone-aware")
        return v

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    priority_id: int
    due_date: Optional[datetime]
    is_completed: bool
    created_at: datetime
    notified_24h: bool = False
    notified_1h: bool = False
    notified_10m: bool = False

    class Config:
        from_attributes = True