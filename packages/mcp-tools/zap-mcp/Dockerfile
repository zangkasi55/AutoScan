FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/zap-mcp /app/zap-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt
ENV PYTHONPATH=/app
# ZAP runs as a sidecar container in the K8s Pod (zaproxy/zap-stable image, port 8090)
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "zap-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
