FROM aquasec/trivy:0.58.0 AS trivy
FROM python:3.12-slim
COPY --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/trivy-mcp /app/trivy-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt
ENV PYTHONPATH=/app
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "trivy-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
