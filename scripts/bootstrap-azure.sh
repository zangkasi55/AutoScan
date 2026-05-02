#!/usr/bin/env bash
# One-shot bootstrap: create Entra app + federated credentials + GitHub secrets.
# Usage: ./scripts/bootstrap-azure.sh [SUB_ID] [REPO]
#
# Prereqs: az (logged in as Owner of the sub), gh (logged in with repo scope).

set -euo pipefail

SUB="${1:-${AZURE_SUBSCRIPTION_ID:-cddad485-52e5-4089-8692-6bb00801606c}}"
REPO="${2:-${GITHUB_REPO:-zangkasi55/AutoScan}}"
APP_NAME="autoscan-github-oidc"

echo "▶ Subscription: $SUB"
echo "▶ Repo:         $REPO"
echo

az account set --subscription "$SUB"
TENANT=$(az account show --query tenantId -o tsv)

# 1. App + SP
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv || true)
if [[ -z "$APP_ID" ]]; then
  APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
  echo "✔ Created app $APP_ID"
else
  echo "✔ Reusing app  $APP_ID"
fi
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
if [[ -z "$SP_ID" ]]; then
  az ad sp create --id "$APP_ID" >/dev/null
fi

# 2. Owner role on the sub (subscription-scope deploy + Defender plans)
az role assignment create \
  --assignee "$APP_ID" \
  --role Owner \
  --scope "/subscriptions/$SUB" \
  --description "AutoScan GH OIDC" 2>/dev/null || echo "  (role already assigned)"

# 3. Federated credentials — main branch + workflow_dispatch on environment=dev
add_fic() {
  local name="$1" subject="$2"
  cat > /tmp/fic.json <<EOF
{ "name": "$name",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "$subject",
  "audiences": ["api://AzureADTokenExchange"] }
EOF
  if az ad app federated-credential list --id "$APP_ID" --query "[?name=='$name']" -o tsv | grep -q .; then
    echo "  (fic '$name' exists)"
  else
    az ad app federated-credential create --id "$APP_ID" --parameters /tmp/fic.json >/dev/null
    echo "✔ Created fic '$name' for subject '$subject'"
  fi
  rm -f /tmp/fic.json
}
add_fic "github-main"          "repo:$REPO:ref:refs/heads/main"
add_fic "github-env-dev"       "repo:$REPO:environment:dev"
add_fic "github-env-staging"   "repo:$REPO:environment:staging"
add_fic "github-env-prod"      "repo:$REPO:environment:prod"
add_fic "github-pull-request"  "repo:$REPO:pull_request"

# 4. Push GH secrets
echo
if command -v gh >/dev/null; then
  gh secret set AZURE_CLIENT_ID       --repo "$REPO" --body "$APP_ID"   >/dev/null
  gh secret set AZURE_TENANT_ID       --repo "$REPO" --body "$TENANT"   >/dev/null
  gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --body "$SUB"      >/dev/null
  echo "✔ GitHub secrets set on $REPO"
else
  echo "⚠ gh not installed — set these secrets manually on $REPO:"
fi

echo
echo "▶ Summary"
echo "  AZURE_CLIENT_ID       = $APP_ID"
echo "  AZURE_TENANT_ID       = $TENANT"
echo "  AZURE_SUBSCRIPTION_ID = $SUB"
echo
echo "Next step:"
echo "  gh workflow run deploy-infra.yml -R $REPO -f environment=dev"
