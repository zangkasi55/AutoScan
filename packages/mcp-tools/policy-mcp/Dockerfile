FROM openpolicyagent/opa:0.65.0-static AS opa

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY --from=opa /opa /usr/local/bin/opa

WORKDIR /app
COPY packages/policy-engine /app/policy
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/policy-mcp /app/policy-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt

# Build the bundle at image build time
RUN opa build -b /app/policy -o /app/bundle.tar.gz

# Run OPA + Uvicorn together
COPY packages/mcp-tools/policy-mcp/supervisord.conf /etc/supervisor/conf.d/policy.conf

ENV PYTHONPATH=/app
ENV OPA_URL=http://localhost:8181
EXPOSE 8080 8181
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
