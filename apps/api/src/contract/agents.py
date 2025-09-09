from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.config import settings

client = genai.Client(
  api_key=settings.GEMINI_API_KEY
)

async def generate_toc(user_request: str):
  # Generate a table of contents for the user's documents
  prompt = f"""
  You are a precise legal paralegal. Based on the user's request, generate a standard Table of Contents 
  for the contract. Return ONLY a JSON array of at least 10 section titles.

  User Request: {user_request}

  Example Output:
  ["1. Introduction", "2. Definitions", "3. Terms and Conditions", "4. Confidentiality", "5. Termination", "6. Governing Law", ...]
  """
  
  response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
      "response_mime_type": "application/json",
      "response_schema": list[str],
    }
  )
  
  contract_sections: list[str] = response.parsed
  return contract_sections


async def write_section(user_request: str, section_title: str):
  print(f"[DEBUG] Starting write_section for: {section_title}")
  prompt = f"""
  You are a senior legal counsel. Write the following section of the contract based on the user's request:
  Section Title: {section_title}
  User Request: {user_request}
  Use formal, clear legal language appropriate for a binding agreement. Avoid placeholders, be specific. Use consistent numbering and subclauses if needed.
  Do not include markdown. Just return plain text.
  """

  @retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Retrying due to: {retry_state.outcome.exception()}"),
  )
  async def call_api():
    response = client.models.generate_content_stream(
      model='gemini-2.5-flash',
      contents=[prompt],
    )
    return response

  try:
    print(f"[DEBUG] Calling Gemini API for section: {section_title}")
    response = await call_api()
    print(f"[DEBUG] Gemini streaming response started for {section_title}")

    # Stream the response chunk by chunk for immediate cancellation responsiveness
    for chunk in response:
      yield chunk.text

  except Exception as e:
    error_msg = f"Error generating section '{section_title}': {e}"
    print(f"[DEBUG] {error_msg}")
    yield error_msg


async def get_title(user_request: str) -> str:
  prompt = f"""
  You are a legal expert. Based on the user's request, generate a title for the contract.
  User Request: {user_request}
  Just Return a one line answer.
  If the title cannot be determined from the request, respond with 'does not contain information to generate a contract title'.
  """

  response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
  )

  return response.text


async def edit_contract(current_content: str, edit_prompt: str):
  """
  Edit a contract based on a user's natural language prompt using Google AI.
  
  Args:
      current_content: The current contract content
      edit_prompt: Natural language description of the desired changes
      
  Yields:
      Chunks of the edited contract content
  """
  
  prompt = f"""
    You are a professional contract editor. Your task is to modify existing contracts based on user instructions.

    IMPORTANT GUIDELINES:
    1. Preserve the overall structure and formatting of the contract
    2. Make only the changes requested by the user
    3. Ensure all modifications are legally sound and professional
    4. Maintain consistency in tone and style with the existing contract
    5. If the requested change would create legal issues, suggest alternatives
    6. Keep all existing clause numbers and headings unless specifically asked to change them
    7. Output the COMPLETE modified contract, not just the changes

    CURRENT CONTRACT:
    {current_content}

    EDIT INSTRUCTION: {edit_prompt}

    Please provide the complete edited contract with the requested modifications. Maintain all formatting and structure while implementing the requested changes.
    """

  @retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"Retrying due to: {retry_state.outcome.exception()}"),
  )
  async def call_api():
    response = client.models.generate_content(
      model='gemini-2.5-flash',
      contents=prompt,
      stream=True  # Enable streaming for immediate responsiveness
    )
    return response

  try:
    print(f"[DEBUG] Calling Gemini API for contract edit: {edit_prompt[:50]}...")
    response = await call_api()
    print(f"[DEBUG] Gemini edit streaming response started")

    # Stream the response chunk by chunk for immediate cancellation responsiveness
    for chunk in response:
      if hasattr(chunk, 'text') and chunk.text:
        yield chunk.text
      elif hasattr(chunk, 'candidates') and chunk.candidates:
        for candidate in chunk.candidates:
          if hasattr(candidate, 'content') and candidate.content:
            for part in candidate.content.parts:
              if hasattr(part, 'text') and part.text:
                yield part.text

  except Exception as e:
    error_msg = f"Error editing contract: {e}"
    print(f"[DEBUG] {error_msg}")
    yield error_msg


async def suggest_edits(current_content: str) -> list[str]:
  """
  Suggest possible edits for a contract using Google AI.
  
  Args:
      current_content: The current contract content
      
  Returns:
      List of suggested edit prompts
  """
  
  prompt = f"""You are a contract review expert. Analyze the given contract and suggest 3-5 common improvements or modifications that might be helpful. 

Provide suggestions as short, actionable prompts that a user could use to edit the contract.

Examples:
- "Make the payment terms more flexible"
- "Add a force majeure clause"
- "Clarify the termination conditions"
- "Add intellectual property protections"
- "Include a dispute resolution clause"

Focus on practical, commonly needed contract improvements. Return ONLY a JSON array of suggestion strings.

CONTRACT TO ANALYZE:
{current_content[:2000]}"""

  try:
    response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt,
      config={
        "response_mime_type": "application/json",
        "response_schema": list[str],
      }
    )
    
    suggestions: list[str] = response.parsed
    return suggestions[:5]  # Return max 5 suggestions
        
  except Exception as e:
    print(f"[DEBUG] Error generating edit suggestions: {e}")
    return ["Add termination clause", "Clarify payment terms", "Include dispute resolution"]