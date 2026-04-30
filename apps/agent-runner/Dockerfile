FROM python:3.12-slim
WORKDIR /app
COPY apps/agent-runner /app/agent-runner
COPY packages/mcp-tools /app/packages/mcp-tools
COPY packages/agent-roles /app/packages/agent-roles
RUN pip install --no-cache-dir -r /app/agent-runner/requirements.txt
ENV PYTHONPATH=/app
EXPOSE 8080
USER 65532:65532
CMD ["python", "-m", "agent-runner.runner"]
