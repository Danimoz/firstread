from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .models import ContractStatus

class ContractCreate(BaseModel):
  prompt: str = Field(..., min_length=1, description="Prompt for contract generation")

class ContractResponse(BaseModel):
  id: UUID
  title: str
  prompt: str
  content: Optional[str] = None
  status: ContractStatus
  user_id: UUID
  created_at: datetime
  completed_at: Optional[datetime] = None
  updated_at: datetime
  
  class Config:
    from_attributes = True

class ContractUpdate(BaseModel):
  title: Optional[str] = None
  content: Optional[str] = None
  status: Optional[ContractStatus] = None
  completed_at: Optional[datetime] = None

class ContractListResponse(BaseModel):
  id: UUID
  title: str
  status: ContractStatus
  created_at: datetime
  completed_at: Optional[datetime] = None
  
  class Config:
    from_attributes = True

class ContractVersionCreate(BaseModel):
  content: str = Field(..., min_length=1, description="Content for the new contract version")

class EditSuggestionsResponse(BaseModel):
  suggestions: List[str] = Field(..., description="List of suggested edits")

class ContractEditRequest(BaseModel):
  edit_prompt: str = Field(..., min_length=1, description="Natural language prompt for contract editing")