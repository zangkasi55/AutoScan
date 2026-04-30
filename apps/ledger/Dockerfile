FROM python:3.12-slim
WORKDIR /app
COPY apps/ledger /app/ledger
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/evidence-mcp /app/evidence-mcp
COPY packages/mcp-tools/redactor /app/redactor
RUN pip install --no-cache-dir -r /app/_common/requirements.txt asyncpg==0.30.0
ENV PYTHONPATH=/app
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "ledger.server:app", "--host", "0.0.0.0", "--port", "8080"]
