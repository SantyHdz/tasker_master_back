from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from app.database import Base

class Task(Base):
    """Task model with notification tracking for n8n integration."""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(String(1000))
    priority_id = Column(SmallInteger, ForeignKey("priorities.id"), nullable=False)
    due_date = Column(TIMESTAMP(timezone=True))
    is_completed = Column(Boolean, default=False, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Columnas para tracking de notificaciones n8n
    notified_24h = Column(Boolean, default=False, nullable=False, server_default="false")
    notified_1h = Column(Boolean, default=False, nullable=False, server_default="false")
    notified_10m = Column(Boolean, default=False, nullable=False, server_default="false")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', due_date={self.due_date})>"