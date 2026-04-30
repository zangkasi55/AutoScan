FROM projectdiscovery/subfinder:v2.6.6 AS sf
FROM projectdiscovery/httpx:v1.6.10 AS hx
FROM python:3.12-slim
COPY --from=sf /usr/local/bin/subfinder /usr/local/bin/subfinder
COPY --from=hx /usr/local/bin/httpx /usr/local/bin/httpx
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/subfinder-mcp /app/subfinder-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt
ENV PYTHONPATH=/app
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "subfinder-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
