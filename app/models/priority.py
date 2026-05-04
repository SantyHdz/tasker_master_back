from sqlalchemy import Column, SmallInteger, String
from app.database import Base

class Priority(Base):
    """Priority model for task categorization."""
    __tablename__ = "priorities"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Priority(id={self.id}, name='{self.name}')>"