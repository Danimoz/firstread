from datetime import datetime

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