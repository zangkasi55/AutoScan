FROM python:3.12-slim
WORKDIR /app
COPY packages/vuln-intel /app/vuln-intel
RUN pip install --no-cache-dir -r /app/vuln-intel/requirements.txt
ENV PYTHONPATH=/app
USER 65532:65532
CMD ["python", "-m", "vuln-intel.ingest"]
