from sqlalchemy import Column, SmallInteger, String
from app.database import Base

class Priority(Base):
    __tablename__ = "priorities"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String, unique=True, nullable=False)