FROM python:3.12-slim

# uv, pinned to the version used locally.
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv

WORKDIR /app
# Compile to bytecode at install time (faster startup); copy files instead of linking to uv's cache.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencies first, as their own layer: Docker reuses it until the lockfile changes,
# so editing app code doesn't reinstall every package.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app

# Don't run as root: if the app were ever compromised, the attacker isn't root in the container.
RUN useradd --create-home appuser
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Production server (no auto-reload). --root-path: nginx serves us under /api,
# so FastAPI links its docs to /api/openapi.json.
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--root-path", "/api"]
