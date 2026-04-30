# AutoScan / Sentry-AI — Agentic Vulnerability Scanner

> **Codename:** Sentry-AI · **Product:** AVS · v0.1 (MVP foundation)

Autonomous, multi-LLM vulnerability scanner that produces **fewer, better-evidenced, exploit-chain-aware findings** in **Thai and English**, with **PDPA-native chain-of-custody** and a **runtime-enforced authorization gate** (RoE).

## Architecture in 60 seconds

- **Orchestrator (Claude Opus 4.7)** plans a scan from a signed RoE.
- **Specialist agents (GPT-5.5)** — Recon, Vuln, Exploit-Reasoning, Critic, Report-Writer — each a separate process with its own role-bound prompt.
- **MCP tool layer** wraps deterministic OSS scanners (Nmap, Nuclei, Trivy, ZAP, Prowler, BloodHound CE, …). LLMs *plan*; OSS *executes*.
- **OPA + Rego** on the hot path: every MCP tool call is authorized against the signed RoE. Out-of-scope = hard fail.
- **Evidence ledger** (Postgres, append-only, Merkle-chained, RFC 3161 anchored) is the legal artifact for PDPA / BoT / PCI / NCSA-CII.
- **Sandbox** (Firecracker microVM; gVisor fallback). Destructive checks evidence-only by default; per-asset opt-in required.

See `02-prd.md`, `05-architecture.md`, `final/github-copilot-build-spec.md`.

## Repository layout

```
apps/
  orchestrator/        Claude Opus planner (Python · Anthropic SDK)
  agent-runner/        Python worker — hosts specialists + MCP clients
  ledger/              Append-only evidence service (Python; Go port deferred)
  api/                 Public REST + WebSocket (Node + Fastify)
  web/                 React 19 + Vite + Tailwind v4 (bilingual EN/TH)

packages/
  shared-schemas/      Zod + JSON Schema (RoE, Finding, Chain, Evidence)
  policy-engine/       OPA Rego bundles — runtime authorization gate
  i18n/                EN + TH bundles + i18n-lint
  mcp-tools/           MCP server adapters (nmap, nuclei, prowler, evidence, policy, …)
  agent-roles/         System prompts + tool-allow-lists per specialist

infra/
  azure/               Bicep IaC (RG 'AutoScan' + AKS + Postgres + Cosmos + AOAI + Defender + Sentinel)
  helm/                Kubernetes 1.30 charts (control / agents / sandbox namespaces)
  otel/                OpenTelemetry collector config
  terraform/           Optional customer-cloud bootstraps

tests/
  unit/  integration/  e2e/  policy/  safety/

docs/                  ADRs, runbooks, model cards
.github/workflows/     OIDC-federated deploy + CI + container build
```

## Quick start

### 1. Bootstrap Azure (one-time)
- Create an Entra ID app registration with **federated credential** for this repo (`zangkasi55/AutoScan` → branch `main`).
- Grant the SP **Owner** on the target subscription (needed because the deployment is subscription-scope and creates the resource group + Defender plans).
- Add GitHub repo secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

### 2. Deploy infrastructure
```bash
gh workflow run deploy-infra.yml -f environment=dev
```
This creates RG **`AutoScan`** in `eastus` with: AKS, ACR, Postgres Flexible, Cosmos DB (Gremlin), Key Vault, Storage, Log Analytics + Sentinel, Application Insights, Azure OpenAI (with `gpt-4o`, `gpt-4o-mini`, `o1-mini`, `text-embedding-3-large` deployments), Front Door, Defender for Cloud (10 plans), and a User-Assigned Managed Identity.

### 3. Deploy applications
```bash
gh workflow run deploy-apps.yml
```

### 4. Local development
```bash
docker compose -f infra/docker-compose.yml up -d
make dev
```

## What this commit ships (v0.1 foundation)

✅ Bicep IaC for the full Azure platform (`infra/azure/`).
✅ GitHub Actions OIDC deploy + CI workflows.
✅ Postgres schema for the Evidence Ledger (Merkle-chained, append-only, with RFC 3161 anchor table) and findings/chains/RoE tables.
✅ OPA Rego authorization gate with unit tests.
✅ Three working MCP servers: `nmap-mcp`, `nuclei-mcp`, `prowler-mcp`.
✅ `evidence-mcp` (ledger writer) and `policy-mcp` (auth gate sidecar).
✅ Orchestrator + 5 specialist agent skeletons (Claude + GPT routing via LiteLLM).
✅ API gateway (Fastify, OIDC, WebSocket scan timeline).
✅ React 19 + Vite + Tailwind v4 + i18next bilingual web shell using brand tokens.
✅ Helm chart skeleton + docker-compose.
✅ Defender for Cloud + Sentinel onboarding.

## What's deferred to v0.2 / Phase 2 (per `known-gaps.md`)

- Full set of 20 MCP servers (only 3 are working in this commit).
- Firecracker microVM sandbox runtime (manifest stubs in place; gVisor fallback documented).
- WebAuthn step-up auth (OIDC scaffolded; WebAuthn flow stubbed).
- AI/LLM-app probes (MITRE ATLAS) — explicitly v1.1.
- Destructive-replay sandbox.

## Safety contracts (non-negotiable)

1. **No scan starts without a signed RoE.** Hard refusal, no override.
2. **OPA gate on every MCP call.** Out-of-scope = abort + audit log.
3. **Critic agent isolation** — independent context, independent vendor (see `apps/agent-runner/critic.py`).
4. **Redact before write** — Thai PII patterns redacted at ledger write path.
5. **Sandbox-or-no-execute** for any tool with side-effect potential.
6. **Bilingual is build-time enforced** — `i18n-lint` blocks CI on EN/TH parity breaks.
7. **No vendor lock** — `model-router-mcp` switches Claude/OpenAI per ADR-2.

## License

Source-available, customer-deployed. (Final license TBD per `00-brief.md`.)
