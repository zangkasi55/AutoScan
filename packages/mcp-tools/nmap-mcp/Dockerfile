FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/nmap-mcp /app/nmap-mcp

RUN pip install --no-cache-dir -r /app/_common/requirements.txt

ENV PYTHONPATH=/app
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "nmap-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
