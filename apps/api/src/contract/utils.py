from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .models import Contract, ContractStatus
from src.users.models import User
from typing import Optional, List

def sse_format(data: str, event: str = None) -> bytes:
  """Formats a string as a Server-Sent Event (SSE).

  Ensures multiline payloads are split into multiple 'data:' lines so that
  compliant SSE parsers (including the simple custom parser in the web app)
  don't drop lines after the first newline.
  """
  msg = ""
  if event:
    msg += f"event: {event}\n"
  # Split data on newlines and emit each line separately per SSE spec
  for line in str(data).splitlines() or [""]:
    msg += f"data: {line}\n"
  msg += "\n"
  return msg.encode("utf-8")


async def create_contract(
    db: AsyncSession, 
    user_id: UUID, 
    title: str, 
    prompt: str
) -> Contract:
    """Create a new contract in the database."""
    contract = Contract(
        title=title,
        prompt=prompt,
        user_id=user_id,
        status=ContractStatus.GENERATING
    )
    db.add(contract)
    await db.flush()  # To get the generated ID
    await db.refresh(contract)
    return contract


async def update_contract_content(
    db: AsyncSession, 
    contract_id: UUID, 
    content: str
) -> Optional[Contract]:
    """Update contract content."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if contract:
        contract.content = content
        contract.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(contract)
    
    return contract


async def complete_contract(
    db: AsyncSession, 
    contract_id: UUID, 
    final_content: str
) -> Optional[Contract]:
    """Mark contract as completed and update final content."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if contract:
        contract.content = final_content
        contract.status = ContractStatus.COMPLETED
        contract.completed_at = datetime.utcnow()
        contract.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(contract)
    
    return contract


async def cancel_contract(
    db: AsyncSession, 
    contract_id: UUID, 
    partial_content: Optional[str] = None
) -> Optional[Contract]:
    """Mark contract as cancelled."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    
    if contract:
        if partial_content:
            contract.content = partial_content
        contract.status = ContractStatus.CANCELLED
        contract.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(contract)
    
    return contract


async def get_contract_by_id(
    db: AsyncSession, 
    contract_id: UUID
) -> Optional[Contract]:
    """Get a contract by ID."""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.user))
        .where(Contract.id == contract_id)
    )
    return result.scalar_one_or_none()


async def get_user_contracts(
    db: AsyncSession, 
    user_id: UUID, 
    limit: int = 50, 
    offset: int = 0
) -> List[Contract]:
    """Get contracts for a specific user."""
    result = await db.execute(
        select(Contract)
        .where(Contract.user_id == user_id)
        .order_by(Contract.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def update_contract(
  db: AsyncSession, 
  contract_id: UUID, 
  updates
) -> Optional[Contract]:
  """Update a contract with provided changes."""
  result = await db.execute(select(Contract).where(Contract.id == contract_id))
  contract = result.scalar_one_or_none()
  
  if not contract:
    return None
  
  # Update fields if provided
  if hasattr(updates, 'title') and updates.title is not None:
    contract.title = updates.title
  
  if hasattr(updates, 'content') and updates.content is not None:
    contract.content = updates.content
  
  if hasattr(updates, 'status') and updates.status is not None:
    contract.status = updates.status
  
  if hasattr(updates, 'completed_at') and updates.completed_at is not None:
    contract.completed_at = updates.completed_at
  
  # Always update the updated_at timestamp
  contract.updated_at = datetime.utcnow()
  
  await db.flush()
  await db.refresh(contract)
  return contract


async def create_contract_version(
  db: AsyncSession,
  original_contract_id: UUID,
  new_content: str,
  user_id: UUID
) -> Optional[Contract]:
  """Create a new version of a contract (for version history)."""
  # Get original contract
  result = await db.execute(select(Contract).where(Contract.id == original_contract_id))
  original = result.scalar_one_or_none()
    
  if not original:
    return None
  
  # Create new contract as a version
  new_contract = Contract(
    title=f"{original.title} (Edited)",
    prompt=original.prompt,
    content=new_content,
    status=ContractStatus.COMPLETED,
    user_id=user_id,
    completed_at=datetime.now(timezone.utc)
  )
    
  db.add(new_contract)
  await db.flush()
  await db.refresh(new_contract)
  return new_contract