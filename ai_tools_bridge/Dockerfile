FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy the entire bridge directory (includes packages/ subdirectory with all ai_tools_*)
COPY ai_tools_bridge/ ./ai_tools_bridge/

# Install bridge with all tool dependencies
WORKDIR /app/ai_tools_bridge
RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "ai_tools_bridge"]
