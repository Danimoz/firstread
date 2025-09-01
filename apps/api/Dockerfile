FROM python:3.12-slim

WORKDIR /src

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock .

# Install project dependencies system-wide using pyproject metadata
RUN uv pip install --system .

# Copy application code
COPY . /src

ENV PYTHONPATH=/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
