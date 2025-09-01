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
    response = client.models.generate_content(
      model='gemini-2.5-flash',
      contents=prompt
    )
    return response

  try:
    print(f"[DEBUG] Calling Gemini API for section: {section_title}")
    response = await call_api()
    print(f"[DEBUG] Gemini response received for {section_title}, length: {len(response.text)}")

    yield response.text

  except Exception as e:
    error_msg = f"Error generating section '{section_title}': {e}"
    print(f"[DEBUG] {error_msg}")
    yield error_msg


async def get_title(user_request: str) -> str:
  prompt = f"""
  You are a legal expert. Based on the user's request, generate a title for the contract.
  User Request: {user_request}
  Just Return a one line answer.
  """

  response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
  )

  return response.text