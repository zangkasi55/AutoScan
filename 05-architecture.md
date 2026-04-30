# 05 — Reference Architecture

**Project:** Agentic Vulnerability Scanner (AVS / *Sentry-AI*)
**Phase:** 1 — design only, no code
**Author:** Architect, one-man-company orchestrator
**Date:** 2026-04-30
**Source grounding:** `research-technical.md` (cited as `[Tn]` here).

---

## 1. Architectural Goals

1. **Auditable autonomy** — every agent decision and every tool call is traceable, hash-anchored, and replayable.
2. **Vendor-portable model layer** — Claude Opus 4.7 + GPT-5.5 today, swappable tomorrow.
3. **Deterministic execution layer** — LLMs plan; battle-tested OSS scanners execute.
4. **PDPA-native data plane** — chain-of-custody, redaction, encryption, retention, access trail.
5. **Hard authorization boundary** — Rules of Engagement (RoE) is enforced at every tool invocation.
6. **Fail-closed safety** — any uncertainty about scope, identity, or destructive impact aborts the action.

## 2. High-Level Diagram (text)

```
                ┌─────────────────────────────────────────────────────────────┐
                │                         WEB UI / CLI                        │
                │   React + Tailwind  ·  Bilingual EN/TH  ·  Real-time SSE    │
                └──────────────┬──────────────────────────────────────────────┘
                               │ REST + WebSocket
                ┌──────────────┴──────────────────────────────────────────────┐
                │                       API GATEWAY                          │
                │   AuthN (OIDC) · AuthZ (RBAC) · Rate limit · Audit         │
                └──────────────┬──────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼─────────────────────────────────────────┐
        │                      │                                         │
        │           ┌──────────▼─────────┐               ┌───────────────▼─────────────┐
        │           │   ORCHESTRATOR     │               │   COMPLIANCE / EVIDENCE     │
        │           │  Claude Opus 4.7   │               │   Ledger (append-only,      │
        │           │  Planner / Critic  │◀── evidence──▶│   hash-chained, encrypted)  │
        │           └──────────┬─────────┘               └─────────────────────────────┘
        │                      │ MCP (JSON-RPC)
        │           ┌──────────┴───────────────────────────────────────────────┐
        │           │            SPECIALIST AGENT POOL (GPT-5.5 family)        │
        │           │  recon · vuln · exploit-reasoning · report-writer · critic │
        │           └──────────┬───────────────────────────────────────────────┘
        │                      │ MCP
        │           ┌──────────┴───────────────────────────────────────────────┐
        │           │                  TOOL SERVER LAYER (MCP servers)         │
        │           │  Nmap · Masscan · Nuclei · Trivy · Grype · Syft · ZAP   │
        │           │  Prowler · ScoutSuite · BloodHound CE · OSV · NVD · KEV │
        │           │  EPSS · Hashcat (gated) · Hydra (gated)                  │
        │           └──────────┬───────────────────────────────────────────────┘
        │                      │ sandboxed exec (Firecracker / gVisor)
        │           ┌──────────▼───────────────────────────────────────────────┐
        │           │            CUSTOMER NETWORK / CLOUD ACCOUNTS             │
        │           └──────────────────────────────────────────────────────────┘
        │
        └── RULES OF ENGAGEMENT (RoE) policy engine ── consulted on every tool call ──▶ ABORT on scope deviation
```

## 3. Components

### 3.1 Orchestrator (Claude Opus 4.7)
- **Responsibility:** plan a scan from a signed RoE; decompose into recon / vuln / exploit-reason / report tasks; manage the long-context evidence pool; final synthesis.
- **State:** stateless per request; reads/writes the Evidence Ledger via MCP server `evidence-mcp`.
- **Pattern:** orchestrator-worker (planner-executor-critic) per Anthropic's published research-system architecture [T3].
- **Token strategy:** subagents return compressed summaries; full artifacts live in Evidence Ledger; planner reads slice-on-demand.

### 3.2 Specialist Agent Pool (GPT-5.5 family)
Five specialist roles, each a separate agent process:

| Agent | Job | Tools (MCP) |
|---|---|---|
| **Recon** | Asset discovery, attack-surface mapping | nmap-mcp, masscan-mcp, subfinder-mcp, httpx-mcp, prowler-mcp, scoutsuite-mcp, sharphound-mcp, azurehound-mcp |
| **Vuln** | Detection across surfaces | nuclei-mcp, trivy-mcp, grype-mcp, syft-mcp, zap-mcp, inspector-mcp, defender-mcp, gcp-scc-mcp, bloodhound-mcp |
| **Exploit-Reason** | Chain reasoning; corroboration; reachability scoring (no destructive payloads) | osv-mcp, nvd-mcp, kev-mcp, epss-mcp, asset-graph-mcp |
| **Report-Writer** | EN+TH bilingual narrative, regulator-pack assembly | i18n-mcp, template-mcp, evidence-mcp |
| **Critic** | Adversarial review; FP suppression; scope-deviation detection | policy-mcp (RoE), evidence-mcp, model-router-mcp |

### 3.3 RoE Policy Engine (the safety boundary)
- **Input:** signed RoE document (JSON Schema validated; signed JWS).
- **Behavior:** every MCP tool call passes through `policy-mcp` middleware that:
  1. Validates target is in scope (CIDR, domain, account, tag).
  2. Checks tool category is allowed (`recon`, `vuln`, `destructive`).
  3. Checks rate-limit and time-window.
  4. Logs decision (allow/deny + reason) to Evidence Ledger.
  5. On deny → aborts the agent's current step + returns structured error to planner.
- **Hard rule:** policy engine is in-band; if it crashes, all scans halt (fail-closed).

### 3.4 Tool Server Layer (MCP servers)
- All wrapped via Model Context Protocol (JSON-RPC 2.0) — the standard substrate, donated to Linux Foundation Dec 2025 [T1][T2].
- Each MCP server is a containerized process with:
  - Typed input schema (target, options, rate caps).
  - Structured output (JSON; raw artifact path; severity hints).
  - Sandboxing — Firecracker microVM or gVisor (per [T26]); ephemeral; no persistent volumes.
  - Outbound network restricted to RoE-listed destinations only.
- **MCP server registry** (initial set, all wrappers; PRs welcome):

| Server | Tool | Surface |
|---|---|---|
| `nmap-mcp` | Nmap | Network discovery |
| `masscan-mcp` | Masscan | High-volume port scan |
| `subfinder-mcp` + `httpx-mcp` | ProjectDiscovery | Subdomain + HTTP probing |
| `nuclei-mcp` | Nuclei | YAML-templated detection |
| `trivy-mcp`, `grype-mcp`, `syft-mcp` | SBOM / SCA | Containers, packages, IaC |
| `zap-mcp` | OWASP ZAP Automation Framework | Web/API DAST |
| `prowler-mcp` | Prowler | Multi-cloud config |
| `scoutsuite-mcp` | ScoutSuite | Multi-cloud audit |
| `bloodhound-mcp` | BloodHound CE | AD / Entra graph |
| `inspector-mcp`, `defender-mcp`, `gcp-scc-mcp` | Cloud-native | First-party cloud findings |
| `osv-mcp`, `nvd-mcp`, `ghsa-mcp`, `kev-mcp`, `epss-mcp` | Vuln intel | Authoritative data |
| `evidence-mcp` | Evidence ledger | Read/write hashed artifacts |
| `policy-mcp` | RoE engine | Authorization decisions |
| `i18n-mcp` | Translation | EN↔TH (with critic review) |
| `model-router-mcp` | LLM routing | Vendor selection per role |
| `hashcat-mcp`, `hydra-mcp` | Cred testing | **GATED** — per-asset RoE opt-in only |

### 3.5 Evidence Ledger
- **Backing:** PostgreSQL with `pgcrypto`, append-only table, Merkle-tree-style chain (each row hashes prev row + content); periodic anchor of chain root to a public timestamp service (RFC 3161) for non-repudiation.
- **Object storage** for raw artifacts (S3-compatible, customer KMS keys).
- **Access:** all reads logged with subject identity (SSO claim), purpose, query.
- **Redaction:** PII detector (Thai citizen ID, phone, email, bank-account format) runs at *write* path; redacted view stored in PG; raw sealed in object store with HSM-wrapped KEK.

### 3.6 Asset Graph
- **Storage:** Neo4j Community (or PostgreSQL with `pgRouting`); decision deferred to Phase-2 architect refinement.
- **Schema:** nodes = assets (host, service, identity, account, container, image, repo); edges = relationships (runs-on, exposes, trusts, deploys, contains).
- **Population:** Recon agent writes; Vuln + Exploit-Reason agents read.
- **Used for:** chain reachability scoring, blast-radius reasoning, tenant-scoped queries.

### 3.7 Web UI / CLI
- **Web UI:** React + Vite + Tailwind v4 + Radix primitives. Bilingual via `i18next` with split EN/TH bundles; brand tokens from `brand/ci-guide.md`.
- **CLI:** Go binary, single static; `avs scope sign`, `avs scan`, `avs report`. CI/CD-friendly.
- **API:** REST (OpenAPI 3.1) + WebSocket for live scan timeline + Webhooks for outbound events.

### 3.8 AuthN / AuthZ
- OIDC (Entra ID, Google Workspace, Okta) via `oidc-client`.
- Step-up MFA (WebAuthn) required for: signing RoE, enabling destructive checks, exporting raw evidence.
- RBAC roles: `viewer`, `analyst`, `roe-signer`, `admin`. Per-tenant scoping enforced at API gateway.

## 4. Data Flow — One End-to-End Scan

1. Analyst uploads scope spec (PDF/Word/JSON) to `/scopes/upload`.
2. Server extracts → structured RoE JSON; analyst reviews in UI; submits for signature.
3. RoE Signer signs (OIDC + WebAuthn) → JWS-wrapped RoE persisted with hash anchored.
4. Analyst clicks **Start Scan** → API enqueues a scan job referencing RoE id.
5. Orchestrator pulls RoE, validates JWS, plans the scan, dispatches Recon agent.
6. Recon agent issues MCP calls to `nmap-mcp` etc.; every call gates through `policy-mcp`.
7. Outputs land in Evidence Ledger with hashes; Asset Graph populated.
8. Vuln agent dispatched; same flow; findings written with EPSS/KEV/SSVC enrichment.
9. Exploit-Reason agent corroborates each high/critical with ≥2 independent signals; promotes or demotes.
10. Critic agent runs adversarial review pass.
11. Report-Writer composes EN+TH report; renders HTML/PDF; assembles regulator pack.
12. Job marked complete; analyst notified.
13. Every step recorded — replayable from Evidence Ledger.

## 5. Architecture Decision Records (ADRs)

### ADR-1 — Adopt MCP as the agent-tool substrate
- **Decision:** All tool integrations are MCP servers; agents are MCP clients.
- **Rationale:** MCP is the standard, donated to Linux Foundation Agentic AI Foundation Dec 2025 [T1][T2]; MITRE ships Caldera MCP plugin Nov 2025 [T36]; vendor-portable; auditable.
- **Status:** Accepted.

### ADR-2 — Multi-vendor LLM (Claude Opus orchestrator + GPT-5.5 specialists)
- **Decision:** Orchestrator/critic on Anthropic; recon/vuln/report-writer specialists on GPT-5.5 family; model-router-mcp manages routing.
- **Rationale:** Reduces correlated prompt-injection failures across a single vendor; AgentDojo evaluations show every model fails on a non-trivial subset of 629 prompt-injection cases [T11].
- **Status:** Accepted.

### ADR-3 — Sandbox every tool call (Firecracker / gVisor)
- **Decision:** No tool runs in the agent's process; each MCP tool runs in a microVM with no host filesystem, no persistent volume, RoE-restricted egress.
- **Rationale:** OWASP LLM06 (Excessive Agency) mitigation; isolation against tool-supply-chain compromise; alignment with NIST AI RMF / AI 600-1 [T19][T21][T22][T26].
- **Status:** Accepted.

### ADR-4 — Evidence Ledger is append-only with Merkle anchoring
- **Decision:** PG-based append-only ledger; every row hashes prev + content; periodic root anchored to public RFC 3161 timestamp.
- **Rationale:** PDPA chain-of-custody; non-repudiation; supports BoT 30-day evidence-pack requirement.
- **Status:** Accepted.

### ADR-5 — Scoring stack = CVSS 4.0 + EPSS + KEV + SSVC + chain-reachability
- **Decision:** Display all five; combine to single 0–100 headline with sub-score breakdown.
- **Rationale:** CVSS alone is insufficient for prioritization; FIRST CVSS 4.0, EPSS daily probability, CISA KEV "must-patch" override, SSVC decision tree [T17][T18][T23][T24].
- **Status:** Accepted.

### ADR-6 — Evidence-only-by-default destructive checks
- **Decision:** No destructive verification (auth-cracking, exploit with side effect) without per-asset RoE opt-in + step-up MFA + capped depth.
- **Rationale:** Project brief safety constraint; OWASP LLM06; "AI slop" reputational defense.
- **Status:** Accepted.

### ADR-7 — On-prem / customer-cloud deployment in v0.1; SaaS deferred
- **Decision:** Single-tenant deployment shape; Helm chart on K8s; or Docker Compose for small.
- **Rationale:** PDPA + BoT data-residency considerations; easier procurement for first Thai customers; reduces infra surface for v0.1.
- **Status:** Accepted.

### ADR-8 — Bilingual (Thai+English) is a build-time enforced contract
- **Decision:** `i18n-lint` runs in CI; missing key in either language fails the build.
- **Rationale:** Thai localization is a primary differentiator; cannot be afterthought.
- **Status:** Accepted.

## 6. Non-Functional Requirements (NFRs)

| Property | Target |
|---|---|
| Scan throughput (recon) | ≥ /16 IPv4 in ≤ 4 hours, configurable rate cap |
| Scan throughput (vuln) | ≥ 1,000 hosts in ≤ 8 hours |
| Time-to-first-finding | ≤ 30 min for /24 scope |
| API p95 latency (UI calls) | < 400 ms |
| Live timeline event lag | < 2 s |
| Evidence write durability | RPO = 0 (synchronous replication or fsync+checkpoint) |
| Encryption at rest | AES-256-GCM with customer-managed keys |
| Encryption in transit | TLS 1.3 minimum |
| Tool sandbox isolation | Firecracker microVM or gVisor; no shared kernel privileges |
| LLM-call observability | 100% of calls logged: prompt, response, tool calls, latency, model id |
| Authorization-gate violations | 0 (HARD) |
| Data residency | Customer-controlled; v0.1 supports th-central-1 / on-prem |
| Multi-tenant isolation | Network + storage namespace per tenant; per-tenant KMS key |

## 7. Technology Stack (preliminary; refine in Phase 2)

- **Backend:** Node.js 22 LTS + TypeScript + Fastify; or Go 1.23 (microservices).
- **Workers:** Python 3.12 (LLM clients, tool wrappers).
- **Databases:** PostgreSQL 16 (primary), Neo4j Community 5 (asset graph), Redis 7 (queues, caches).
- **Object storage:** S3-compatible (MinIO on-prem; Azure Blob / S3 on cloud).
- **Sandbox runtime:** Firecracker (preferred); gVisor fallback.
- **Orchestration:** Kubernetes 1.30 + Helm; or Docker Compose for small.
- **Frontend:** React 19 + Vite + Tailwind v4 + Radix; i18next.
- **Observability:** OpenTelemetry; Tempo (traces) + Loki (logs) + Prometheus (metrics) + Grafana.
- **MCP runtime:** official MCP TypeScript / Python SDKs.
- **Secrets / KMS:** HashiCorp Vault on-prem; Azure Key Vault / AWS KMS managed.

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Prompt-injection via attacker-controlled scan target content (e.g., HTML title containing prompts) | Strict input sanitization on all tool outputs before they enter LLM context; critic-agent adversarial review; AgentDojo-style regression tests in CI |
| Tool-supply-chain compromise (poisoned Nuclei template) | Pin templates; signature-verify; sandbox; outbound egress allowlist |
| Customer-controlled key loss = evidence loss | Documented key-rotation + escrow workflow; encrypted backups |
| LLM vendor outage | model-router-mcp falls back to alternate vendor for that role |
| Scope-deviation false-positive (legit asset newly added) | RoE versioning + diff review; agent pauses for analyst confirmation before scanning new assets |
| PDPA dispute over evidence retention | Retention policy is per-tenant and customer-configurable; cryptographic erase on hard-delete |

## 9. Phase-2 Refinements Expected

- Final choice between Neo4j and PG-pgRouting for asset graph (benchmark on 100k-node).
- Final choice of message bus (NATS vs Redis Streams vs Kafka) for agent events.
- Concrete Helm chart layout + Docker Compose for self-host SKU.
- Per-tenant KMS key model; HSM integration plan.
- AI/LLM-application probe surface (MITRE ATLAS) — moved to v1.1 per PRD §6.
