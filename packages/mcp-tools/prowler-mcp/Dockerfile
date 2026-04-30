FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl gnupg lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI (Prowler reuses it for auth) and AWS CLI v2.
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
 && curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/aws.zip \
 && apt-get install -y unzip && unzip -q /tmp/aws.zip -d /tmp \
 && /tmp/aws/install && rm -rf /tmp/aws /tmp/aws.zip

# Prowler (multi-cloud) — pin a known release.
RUN pip install --no-cache-dir prowler==5.6.0

WORKDIR /app
COPY packages/mcp-tools/_common /app/_common
COPY packages/mcp-tools/prowler-mcp /app/prowler-mcp
RUN pip install --no-cache-dir -r /app/_common/requirements.txt

ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "prowler-mcp.server:app", "--host", "0.0.0.0", "--port", "8080"]
