# MCP Server Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code (includes start.sh and mcp_tools.py)
COPY mcp-server/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Ensure startup script is executable
RUN chmod +x start.sh

# Expose ports: REST API + MCP SSE protocol
EXPOSE 8001 8002

# Health check against REST API
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run both servers (REST on 8001, MCP SSE on 8002)
CMD ["./start.sh"]
