import uuid, logging, asyncio
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session as get_db
from src.users.utils import JWTBearer
from .agents import generate_toc, get_title, write_section
from .utils import sse_format
from .schema import ContractCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active contract generation tasks
active_contracts = {}

router = APIRouter(
  prefix="/contracts",
  tags=["contracts"],
  dependencies=[Depends(JWTBearer())]
)

@router.post("/")
async def create_contract(request: Request, contract_data: ContractCreate):
  contract_id = str(uuid.uuid4())
  contract_title = await get_title(contract_data.prompt)
  
  # Create cancellation token
  cancel_event = asyncio.Event()
  active_contracts[contract_id] = cancel_event
  
  async def generate():
    try:
      sections = await generate_toc(contract_data.prompt)

      # Send contract ID and title first
      yield sse_format(f'{{"contract_id": "{contract_id}"}}', event="contract_id")
      yield sse_format(f"<h1>{contract_title}</h1>\n")
      yield sse_format("<div class='contract-body'>")

      for idx, title in enumerate(sections, start=1):
        # Check if cancelled
        if cancel_event.is_set():
          yield sse_format("Generation cancelled by user", event="cancelled")
          break
          
        # Check if client disconnected
        if await request.is_disconnected():
          logger.info(f"Client disconnected for contract {contract_id}")
          break

        yield sse_format(f"<h2>{title}</h2>")
        yield sse_format("<p>")

        try:
          logger.info(f"Starting section generation for: {title}")
          section_chunks = []
          async for chunk in write_section(contract_data.prompt, title):
            # Check cancellation frequently during generation
            if cancel_event.is_set():
              yield sse_format("Generation cancelled by user", event="cancelled")
              return
            logger.info(f"Generated chunk for {title}: {chunk[:50]}...")
            section_chunks.append(chunk)
            yield sse_format(chunk)
          
          logger.info(f"Completed section '{title}' with {len(section_chunks)} chunks")
        except Exception as e:
          logger.error(f"Error generating section '{title}': {e}")
          yield sse_format(f"Error in section '{title}': {str(e)}")

        yield sse_format("</p>")

      if not cancel_event.is_set():
        yield sse_format("</div>")
        yield sse_format(f"<p><strong>Contract {contract_id} completed.</strong></p>", event="done")
    finally:
      # Clean up
      if contract_id in active_contracts:
        del active_contracts[contract_id]
  
  return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/{contract_id}/stop")
async def stop_contract_generation(contract_id: str):
  """Stop an active contract generation"""
  if contract_id not in active_contracts:
    raise HTTPException(
      status_code=404, 
      detail=f"Contract {contract_id} not found or already completed"
    )
  
  # Signal cancellation
  active_contracts[contract_id].set()
  logger.info(f"Contract generation {contract_id} stopped by user")
  
  return {"message": f"Contract generation {contract_id} stopped successfully"}

