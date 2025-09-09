# --- Builder Stage ---
# This stage installs dependencies and builds the application
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /src
# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project --no-dev

COPY . /src
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev


FROM python:3.12-alpine

COPY --from=builder --chown=app:app /src /src
# Place executables in the environment at the front of the path
ENV PATH="/src/.venv/bin:$PATH"

# CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
CMD fastapi run src/src/main.py --host 0.0.0.0 --port $PORT