FROM projectdiscovery/nuclei:v3.3.5 AS nuclei

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=nuclei /usr/local/bin/nuclei /usr/local/bin/nuclei

# Pin templates to a known commit (override at build time via --build-arg).
ARG NUCLEI_TEMPLATES_REF=main
RUN git clone --depth=1 --branch ${NUCLEI_TEMPLATES_REF} \
    https://github.com/projectdiscovery/nuclei-templates.git /opt/nuclei-templates \
 && rm -rf /opt/nuclei-templates/.git

WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/nuclei-mcp /app/nuclei-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt

ENV PYTHONPATH=/app
ENV NUCLEI_TEMPLATES_DIR=/opt/nuclei-templates
EXPOSE 8080
USER 65532:65532
CMD ["uvicorn", "nuclei-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
