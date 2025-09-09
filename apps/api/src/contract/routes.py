import uuid, logging, asyncio
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session as get_db
from src.users.utils import JWTBearer, get_current_user
from src.users.models import User
from .agents import generate_toc, get_title, write_section, edit_contract, suggest_edits
from .utils import (
  sse_format, 
  create_contract, 
  update_contract_content, 
  complete_contract, 
  cancel_contract,
  get_contract_by_id,
  get_user_contracts,
  update_contract,
  create_contract_version
)
from .schema import (
  ContractCreate, 
  ContractResponse, 
  ContractListResponse, 
  ContractUpdate, 
  ContractVersionCreate, 
  ContractEditRequest, 
  EditSuggestionsResponse
)
from .models import ContractStatus
from typing import List
from uuid import UUID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active contract generation tasks
active_contracts = {}

router = APIRouter(
  prefix="/contracts",
  tags=["contracts"],
  dependencies=[Depends(JWTBearer())]
)

async def get_current_user_from_token(
  token: str = Depends(JWTBearer()),
  db: AsyncSession = Depends(get_db)
) -> User:
  """Get current user from JWT token"""
  user = await get_current_user(db, token)
  if not user:
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")
  return user

@router.post("/")
async def create_contract_route(
  request: Request, 
  contract_data: ContractCreate,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user_from_token)
):
  contract_title = await get_title(contract_data.prompt)
  
  if "does not contain information to generate a contract title" in contract_title:
      raise HTTPException(status_code=400, detail="Prompt does not contain sufficient information to generate a contract title")

  # Create contract in database
  contract = await create_contract(
    db=db,
    user_id=current_user.id,
    title=contract_title,
    prompt=contract_data.prompt
  )
  await db.commit()
  
  contract_id = str(contract.id)
  
  # Create cancellation token
  cancel_event = asyncio.Event()
  active_contracts[contract_id] = cancel_event
  
  async def generate():
    content_buffer = ""
    try:
      sections = await generate_toc(contract_data.prompt)
      
      # Send contract ID and title first
      yield sse_format(f'{{"contract_id": "{contract_id}"}}', event="contract_id")
      yield sse_format(f"<h1>{contract_title}</h1>\n")
      content_buffer += f"<h1>{contract_title}</h1>\n"
      
      yield sse_format("<div class='contract-body'>")
      content_buffer += "<div class='contract-body'>"

      for idx, title in enumerate(sections, start=1):
        # Check if cancelled
        if cancel_event.is_set():
          # Save partial content before cancelling
          await cancel_contract(db, contract.id, content_buffer)
          await db.commit()
          yield sse_format("Generation cancelled by user", event="cancelled")
          break
            
          # Check if client disconnected
        if await request.is_disconnected():
          logger.info(f"Client disconnected for contract {contract_id}")
          await cancel_contract(db, contract.id, content_buffer)
          await db.commit()
          break

        section_title = f"<h2>{title}</h2>"
        yield sse_format(section_title)
        content_buffer += section_title
        
        yield sse_format("<p>")
        content_buffer += "<p>"

        try:
          logger.info(f"Starting section generation for: {title}")
          section_chunks = []
          async for chunk in write_section(contract_data.prompt, title):
            # Check cancellation IMMEDIATELY for each chunk
            if cancel_event.is_set():
              logger.info(f"Cancellation detected during section '{title}' generation")
              await cancel_contract(db, contract.id, content_buffer)
              await db.commit()
              yield sse_format("Generation cancelled by user", event="cancelled")
              return
            
            # Check if client disconnected
            if await request.is_disconnected():
              logger.info(f"Client disconnected during section '{title}' generation")
              await cancel_contract(db, contract.id, content_buffer)
              await db.commit()
              return
            
            logger.info(f"Generated chunk for {title}: {chunk[:50]}...")
            section_chunks.append(chunk)
            content_buffer += chunk
            yield sse_format(chunk)
            
            # Periodically update database with current content (less frequently to avoid overhead)
            if len(section_chunks) % 10 == 0:  # Update every 10 chunks instead of 5
              await update_contract_content(db, contract.id, content_buffer)
              await db.commit()

          logger.info(f"Completed section '{title}' with {len(section_chunks)} chunks")
        except Exception as e:
          logger.error(f"Error generating section '{title}': {e}")
          error_msg = f"Error in section '{title}': {str(e)}"
          yield sse_format(error_msg)
          content_buffer += error_msg

        yield sse_format("</p>")
        content_buffer += "</p>"

      if not cancel_event.is_set():
        yield sse_format("</div>")
        content_buffer += "</div>"
        
        completion_msg = f"<p><strong>Contract {contract_id} completed.</strong></p>"
        yield sse_format(completion_msg, event="done")
        content_buffer += completion_msg
        
        # Mark contract as completed in database
        await complete_contract(db, contract.id, content_buffer)
        await db.commit()
            
    except Exception as e:
      logger.error(f"Error in contract generation: {e}")
      await cancel_contract(db, contract.id, content_buffer)
      await db.commit()
      yield sse_format(f"Generation failed: {str(e)}", event="error")
    finally:
      # Clean up
      if contract_id in active_contracts:
        del active_contracts[contract_id]
  
  return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/{contract_id}/stop")
async def stop_contract_generation(
  contract_id: str,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user_from_token)
):
  """Stop an active contract generation or edit operation"""
  # Verify contract belongs to current user
  contract = await get_contract_by_id(db, UUID(contract_id))
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to stop this contract")
  
  stopped_operations = []
  
  # Check for active generation
  if contract_id in active_contracts:
    active_contracts[contract_id].set()
    stopped_operations.append("generation")
    logger.info(f"Contract generation {contract_id} stopped by user")
  
  # Check for active edit operations
  edit_keys = [key for key in active_contracts.keys() if key.startswith(f"edit_{contract_id}_")]
  for edit_key in edit_keys:
    active_contracts[edit_key].set()
    stopped_operations.append("edit")
    logger.info(f"Contract edit {edit_key} stopped by user")
  
  if not stopped_operations:
    raise HTTPException(status_code=404, detail=f"No active operations found for contract {contract_id}")

  operations_text = " and ".join(stopped_operations)
  return {"message": f"Contract {operations_text} stopped successfully"}


@router.get("/", response_model=List[ContractListResponse])
async def get_user_contracts_route(
  limit: int = 50,
  offset: int = 0,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user_from_token)
):
  """Get contracts for the current user"""
  contracts = await get_user_contracts(db, current_user.id, limit, offset)
  return contracts


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract_route(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
  """Get a specific contract by ID"""
  contract = await get_contract_by_id(db, contract_id)
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to access this contract")
  
  return contract


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract_route(
    contract_id: UUID,
    updates: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
  """Update a contract"""
  # Verify contract exists and belongs to user
  contract = await get_contract_by_id(db, contract_id)
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to edit this contract")
  
  # Update the contract
  updated_contract = await update_contract(db, contract_id, updates)
  if not updated_contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  await db.commit()
  return updated_contract


@router.post("/{contract_id}/versions", response_model=ContractResponse)
async def create_contract_version_route(
    contract_id: UUID,
    updates: ContractVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
  """Create a new version of a contract (preserves original)"""
  # Verify contract exists and belongs to user
  contract = await get_contract_by_id(db, contract_id)
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to edit this contract")
  
  if not updates.content:
    raise HTTPException(status_code=400, detail="Content is required for creating a new version")
  
  # Create new version
  new_version = await create_contract_version(
    db, contract_id, updates.content, current_user.id
  )
  if not new_version:
    raise HTTPException(status_code=404, detail="Failed to create contract version")
  
  await db.commit()
  return new_version


@router.post("/{contract_id}/edit")
async def edit_contract_route(
    request: Request,
    contract_id: UUID,
    edit_data: ContractEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
  """Edit a contract using LLM based on natural language prompt"""
  # Verify contract exists and belongs to user
  contract = await get_contract_by_id(db, contract_id)
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to edit this contract")
  
  if not contract.content:
    raise HTTPException(status_code=400, detail="Contract has no content to edit")
  
  edit_prompt = edit_data.edit_prompt.strip()
  if not edit_prompt:
    raise HTTPException(status_code=400, detail="Edit prompt is required")
  
  # Create cancellation token for this edit
  edit_id = f"edit_{contract_id}_{int(asyncio.get_event_loop().time())}"
  cancel_event = asyncio.Event()
  active_contracts[edit_id] = cancel_event
  
  async def generate_edit():
    content_buffer = ""
    try:
      # Send edit started event
      yield sse_format(f'{{"edit_id": "{edit_id}"}}', event="edit_started")
      
      async for chunk in edit_contract(contract.content, edit_prompt):
        # Check if cancelled IMMEDIATELY for each chunk
        if cancel_event.is_set():
          logger.info(f"Edit cancellation detected for edit {edit_id}")
          yield sse_format("Edit cancelled by user", event="cancelled")
          break
          
        # Check if client disconnected
        if await request.is_disconnected():
          logger.info(f"Client disconnected for edit {edit_id}")
          break
          
        content_buffer += chunk
        yield sse_format(chunk)
      
      if not cancel_event.is_set():
        # Create new version with edited content
        new_version = await create_contract_version(
          db, contract_id, content_buffer, current_user.id
        )
        await db.commit()
        
        completion_msg = f'{{"new_contract_id": "{new_version.id}"}}'
        yield sse_format(completion_msg, event="edit_complete")
        
    except Exception as e:
      logger.error(f"Error in contract editing: {e}")
      yield sse_format(f"Edit failed: {str(e)}", event="error")
    finally:
      # Clean up
      if edit_id in active_contracts:
        del active_contracts[edit_id]
  
  return StreamingResponse(generate_edit(), media_type="text/event-stream")


@router.get("/{contract_id}/suggestions", response_model=EditSuggestionsResponse)
async def get_edit_suggestions_route(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
  """Get suggested edits for a contract"""
  # Verify contract exists and belongs to user
  contract = await get_contract_by_id(db, contract_id)
  if not contract:
    raise HTTPException(status_code=404, detail="Contract not found")
  
  if contract.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to access this contract")
  
  if not contract.content:
    raise HTTPException(status_code=400, detail="Contract has no content to analyze")
  
  try:
    suggestions = await suggest_edits(contract.content)
    return EditSuggestionsResponse(suggestions=suggestions)
  except Exception as e:
    logger.error(f"Error generating suggestions: {e}")
    raise HTTPException(status_code=500, detail="Failed to generate suggestions")

