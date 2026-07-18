# Shared image for the pipeline (one-shot), backend, and MCP server —
# they're the same dependency set, only the CMD differs per service in
# docker-compose.yml.

FROM python:3.11-slim

# xgboost's compiled extension needs libgomp at runtime; slim doesn't ship it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY intelligence/ intelligence/
COPY platform/backend/ platform/backend/
COPY platform/mcp_server/ platform/mcp_server/
COPY platform/rag/ platform/rag/

CMD ["python", "platform/backend/main.py"]
