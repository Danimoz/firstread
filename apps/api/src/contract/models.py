from sqlalchemy import UUID, Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.core.database import Base

class ContractStatus(enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(500), nullable=False)
    prompt = Column(Text, nullable=False)
    content = Column(Text, nullable=True)  # HTML content of the contract
    status = Column(Enum(ContractStatus), default=ContractStatus.GENERATING, nullable=False)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="contracts")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
      return f"<Contract(id={self.id}, title='{self.title}', status={self.status.value})>"