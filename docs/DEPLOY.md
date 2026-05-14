# Deploy AutoScan to Azure (RG: AutoScan)

This guide walks through deploying the AVS / Sentry-AI platform to your Azure subscription.

## Prerequisites

- Azure subscription (this repo is wired to `0fdda5f4-0853-4336-8f41-0370176387f5`).
- Owner permission on the subscription (the deployment is **subscription-scoped** and creates a new resource group, role assignments, and Defender plans).
- GitHub repo `zangkasi55/AutoScan`.

## 1. Create a federated credential for GitHub Actions (one-time)

```bash
SUB=0fdda5f4-0853-4336-8f41-0370176387f5
az login
az account set --subscription $SUB

# Create app + service principal
APP=$(az ad app create --display-name autoscan-github --query appId -o tsv)
az ad sp create --id $APP

# Owner role at subscription scope (needed for sub-scope Bicep + Defender plans)
az role assignment create --assignee $APP --role Owner --scope "/subscriptions/$SUB"

# Federated credential — GitHub OIDC
cat > fic.json <<EOF
{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:zangkasi55/AutoScan:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}
EOF
az ad app federated-credential create --id $APP --parameters fic.json

# Add a second one for workflow_dispatch from any branch (optional)
cat > fic2.json <<EOF
{
  "name": "github-workflows",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:zangkasi55/AutoScan:environment:dev",
  "audiences": ["api://AzureADTokenExchange"]
}
EOF
az ad app federated-credential create --id $APP --parameters fic2.json

echo "AZURE_CLIENT_ID=$APP"
echo "AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)"
```

Add these as **GitHub repo secrets** under Settings → Secrets and variables → Actions:

- `AZURE_CLIENT_ID` — the App ID from above
- `AZURE_TENANT_ID` — your Entra tenant
- (subscription is in the workflow env: `AZURE_SUBSCRIPTION_ID=0fdda5f4-…`)

## 2. Run the infrastructure deployment

```bash
gh workflow run deploy-infra.yml -f environment=dev
gh run watch
```

Or manually:

```bash
az deployment sub create \
  --name autoscan-dev-1 \
  --location eastus \
  --template-file infra/azure/main.bicep \
  --parameters infra/azure/main.parameters.json \
  --parameters environment=dev
```

What gets created in RG `AutoScan`:

| Resource | Purpose |
|----------|---------|
| AKS (Standard tier, 3 zones) | Hosts orchestrator, specialists, MCP servers |
| ACR (Premium) | Signed image registry |
| Postgres Flexible 16 | Evidence ledger + findings |
| Cosmos DB (Gremlin, serverless) | Asset graph |
| Key Vault | Secrets, KMS-wrapped keys |
| Storage (GRS, infra-encrypted) | Sealed evidence + reports + RoE docs |
| Log Analytics + **Microsoft Sentinel** | SIEM + audit |
| Application Insights | OpenTelemetry traces/metrics |
| Azure OpenAI | `gpt-4o`, `gpt-4o-mini`, `o1-mini`, `text-embedding-3-large` |
| Front Door Standard | Public ingress |
| User-Assigned Managed Identity | Workload identity for AKS pods |
| **Defender for Cloud** (10 plans) | CSPM, VMs, Containers, KV, Storage, SQL, Cosmos, App Services, ARM, API |

Subscription-scope changes:
- `Microsoft.Security/pricings` — 10 Defender plans set to Standard
- `Microsoft.Security/workspaceSettings` — security data → the new Log Analytics workspace
- `Microsoft.Security/autoProvisioningSettings` — auto-provision agent on VMs

## 3. Deploy the applications

```bash
gh workflow run deploy-apps.yml -f environment=dev
```

This builds + pushes container images to ACR, then runs `helm upgrade --install` against the AKS cluster.

## 4. Verify

```bash
# Get AKS creds
az aks get-credentials -g AutoScan -n $(az aks list -g AutoScan --query "[0].name" -o tsv)

kubectl get pods -n autoscan
kubectl logs -l app.kubernetes.io/component=api -n autoscan

# Get the public IP of the ingress / LoadBalancer
kubectl get svc -n autoscan
```

Defender for Cloud findings will start populating within ~30 min in the Azure portal under Defender for Cloud → Recommendations.

## 5. Local development

```bash
docker compose -f infra/docker-compose.yml up -d
# Web → http://localhost:5173
# API → http://localhost:8080/healthz
# Postgres → localhost:5432 (avsadmin/avsadmin)
```

## Existing-resource reuse

If you already have a Log Analytics workspace or Azure OpenAI resource, set:

- `existingLogAnalyticsId` — full resource id, e.g. `/subscriptions/.../workspaces/myworkspace`
- `existingOpenAIId` — full resource id

in `infra/azure/main.parameters.json`. The Bicep skips creating new ones.

## Cost guardrails

- AKS: Base tier, 2 system nodes + autoscaling user pool (D4ds_v5). ~$300–600/mo idle.
- Cosmos serverless: pay-per-RU.
- Azure OpenAI deployments: GlobalStandard SKU, throttle by `capacity` parameter.
- Defender plans: enable per-subscription. Disable individual plans by editing `infra/azure/modules/defender.bicep` if needed.

## Teardown

```bash
az group delete -n AutoScan --yes --no-wait
# Disable Defender plans (subscription scope) to stop billing
for p in CloudPosture VirtualMachines StorageAccounts SqlServers KeyVaults Containers AppServices Arm Api CosmosDbs; do
  az security pricing create --name $p --tier Free
done
```
