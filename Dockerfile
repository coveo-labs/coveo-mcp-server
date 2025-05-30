FROM python:3.12-slim

# Install uv
RUN pip install uv

WORKDIR /app
ENV PYTHONPATH=/app/src

COPY . .

# Install dependencies
RUN uv pip install --system --requirements pyproject.toml

# Set environment defaults
ENV USE_STDIO=false

# Run the MCP server using the updated entry point
CMD ["python", "src/coveo_mcp_server/__main__.py"]