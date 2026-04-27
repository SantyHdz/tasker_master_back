from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String)
    priority_id = Column(SmallInteger, ForeignKey("priorities.id"), nullable=False)
    due_date = Column(TIMESTAMP(timezone=True))
    is_completed = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())