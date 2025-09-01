import uuid
from src.core.database import Base
from sqlalchemy import UUID, Boolean, Column, DateTime, String
from sqlalchemy.sql import func

class User(Base):
  __tablename__ = "users"
  id = Column(
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True
  )
  email = Column(String, unique=True, index=True, nullable=False)
  password = Column(String, nullable=False)
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)