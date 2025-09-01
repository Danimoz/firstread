from pydantic import BaseModel

class ContractCreate(BaseModel):
  prompt: str

class ContractResponse(BaseModel):
  id: str
  title: str
  sections: list[str]