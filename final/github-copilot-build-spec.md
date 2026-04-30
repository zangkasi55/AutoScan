# AVS — GitHub Copilot Build Spec

> **Audience:** GitHub Copilot (and human engineers pairing with it). This document is the source of truth for implementing the **Agentic Vulnerability Scanner (AVS)** v0.1 MVP. It compresses the PRD, architecture, and UX into a build-runnable spec.
>
> **Read order before generating any code:**
> 1. `02-prd.md` (product requirements)
> 2. `05-architecture.md` (8 ADRs)
> 3. `04-ux-package/wireframes.md` + `04-ux-package/mockups/*.html`
> 4. This file.
>
> **Ground rule for Copilot:** every safety-relevant claim in this spec is non-negotiable. If a generated implementation removes an authorization check, sandbox boundary, or evidence-anchor step "for simplicity", treat it as a defect.

---

## 0. Project metadata

```
project        : agentic-vuln-scanner (AVS)
codename       : Sentry-AI
version        : 0.1.0 (MVP)
target market  : Thailand enterprise security teams, MSSPs, internal red teams
deployment     : on-prem or customer-cloud (no SaaS in v0.1)
license posture: source-available, customer-deployed
languages      : English + Thai (bilingual is a build-time contract, not a feature)
regulators     : PDPA · BoT cyber-resilience · PCI DSS 4.0 · NCSA / CII reporting
```

---

## 1. Repository layout (target)

```
avs/
├── apps/
│   ├── orchestrator/          # Node.js 22 + Fastify · the planner/arbiter
│   ├── agent-runner/          # Python 3.12 worker that hosts MCP tool calls
│   ├── ledger/                # Append-only evidence service (Go 1.23) · Merkle + RFC 3161
│   ├── api/                   # Public REST + WebSocket gateway (Node + Fastify)
│   └── web/                   # React 19 + Vite + Tailwind v4 (UI)
├── packages/
│   ├── shared-schemas/        # Zod + JSON Schema · RoE, Finding, Chain, Evidence
│   ├── policy-engine/         # OPA + Rego bundles · runtime authorization
│   ├── i18n/                  # EN+TH bundles · build-time lint
│   └── mcp-tools/             # MCP server adapters (nmap, nuclei, trivy, zap, etc.)
├── infra/
│   ├── helm/                  # Kubernetes 1.30 charts
│   ├── terraform/             # Optional customer-cloud bootstraps
│   └── otel/                  # OpenTelemetry collector config
├── docs/                      # PRD, ADRs, runbooks
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    ├── policy/                # Rego unit tests · authorization gate
    └── safety/                # AgentDojo-style red-team prompts
```

---

## 2. Tech stack — exact versions Copilot must target

| Layer | Choice | Version | Rationale |
|------|--------|---------|-----------|
| Orchestrator runtime | Node.js | 22 LTS | Fastify ecosystem, native fetch, mature MCP SDK |
| Orchestrator framework | Fastify | 5.x | Hooks-first, schema-validated, pluggable |
| Agent worker runtime | Python | 3.12 | Mature MCP server libs, asyncio for fan-out |
| Frontend | React | 19 | Concurrent rendering, Suspense for streaming events |
| Build | Vite | 5.x | Fast HMR, ESM-first |
| Styling | Tailwind | v4 | Token-first; matches `brand/ci-guide.md` palette |
| Primary DB | PostgreSQL | 16 | Append-only ledger + scan metadata |
| Graph DB | Neo4j | 5 | Attack-chain reachability queries |
| Cache / queue | Redis | 7 | Agent task queue, rate-limit state |
| Container orchestrator | Kubernetes | 1.30 | Helm v3 charts, 3 namespaces (control / agents / sandbox) |
| Sandbox primary | Firecracker | latest | Destructive-replay isolation; KVM-capable hosts |
| Sandbox fallback | gVisor | latest | For non-KVM clusters |
| Observability | OpenTelemetry | 1.30+ | OTLP traces, metrics, logs to customer's stack |
| Auth (admin) | OIDC via Entra ID | — | SSO + MFA |
| Step-up auth | WebAuthn (FIDO2) | — | Required for RoE signing |
| Policy engine | OPA + Rego | 0.65+ | Authorization gate evaluation |
| Multi-LLM SDK | LiteLLM (or in-house wrapper) | latest | Cross-vendor routing |
| LLM providers | Anthropic Claude · OpenAI GPT | — | Per ADR-2 (vendor diversity) |
| MCP SDK | @modelcontextprotocol/sdk | latest | Reference SDK; matches MCP donation to LF (Dec 2025) |

Pin all dependency versions in `package.json` / `requirements.txt`. Use `npm ci` / `pip install --require-hashes`.

---

## 3. Multi-LLM agent architecture

### 3.1 Roles, primary models, fallbacks (ADR-2)

| Role | Primary | Fallback | Job description (single-line) |
|------|---------|----------|-------------------------------|
| Orchestrator | Claude Opus 4.7 | GPT-5.5 Pro | Decompose RoE-bound goals into agent tasks; arbitrate disagreements; replan. |
| Recon specialist | GPT-5.5 | Claude Haiku 4.5 | Surface mapping, enumeration, asset discovery via read-only MCP tools. |
| Vuln specialist | GPT-5.5 | Claude Sonnet 4.6 | CVE / misconfig probing using Nuclei / Trivy / ZAP / Prowler / ScoutSuite. |
| Exploit-Reasoning | Claude Opus 4.7 | GPT-5.5 Pro | Validate exploit chains via sandboxed replay; never run destructive payload against the live target. |
| Critic | GPT-5.5 | Claude Sonnet 4.6 | Independent re-derivation of findings; FP suppression. **Must run with no shared context** with the agent that produced the finding (G2 in `known-gaps.md`). |
| Report-Writer | GPT-5.5 | Claude Sonnet 4.6 | Bilingual EN+TH narrative generation; regulator-bundle assembly. |

### 3.2 Critic isolation contract (Copilot must implement this exactly)

```ts
// packages/orchestrator/src/critic.ts
export async function runCritic(finding: Finding): Promise<CriticVerdict> {
  // 1. Build a *fresh* context — NO orchestrator history, NO original-agent prompt.
  const ctx = buildCriticContext({
    sceneFacts: finding.evidenceRefs.map(loadAsAttestation), // signed evidence rows only
    targetHypothesis: finding.title,            // never the original prompt
    forbiddenInputs: ['orchestrator_history', 'producing_agent_messages']
  });
  // 2. Use the *fallback vendor* if the original was the primary, else primary.
  const model = selectIndependentModel(finding.producedBy.model);
  // 3. Ask: "Given these signed evidence attestations, can you re-derive this conclusion?"
  return await llm.complete(ctx, model, { temperature: 0.1 });
}
```

If Copilot generates a Critic that pulls from the orchestrator history, **reject the diff.**

### 3.3 Model router (`packages/policy-engine/router.ts`)

- Per-call inputs: `{role, taskKind, tokensEstimated}`.
- Output: `{provider, model, fallback}`.
- Settings UI binding: `apps/web/src/pages/settings/models.tsx` reads/writes a config CRD.
- Failover triggers: HTTP 429, HTTP 5xx, timeout > role-specific limit.
- All calls emit OTel spans `llm.call` with attributes `{role, provider, model, tokens.in, tokens.out, latency.ms}`.

---

## 4. Authorization & RoE — the single most important subsystem

### 4.1 RoE schema (`packages/shared-schemas/roe.ts`)

```ts
export const RoESchema = z.object({
  id: z.string().uuid(),
  tenantId: z.string(),
  scope: z.object({
    cidrs: z.array(z.string().regex(CIDR)),
    hosts: z.array(z.string()),
    cloudAccounts: z.array(z.object({provider: z.enum(['aws','azure','gcp']), id: z.string(), tagFilter: z.string().optional()}))
  }),
  exclusions: z.object({
    cidrs: z.array(z.string().regex(CIDR)),
    hosts: z.array(z.string()),
    tags: z.array(z.string())
  }),
  testCategories: z.array(z.enum(['recon','cve','webapp','ad','chain','dos'])),
  destructiveOptIns: z.array(z.object({asset: z.string(), allow: z.boolean(), justification: z.string()})),
  timeWindow: z.object({startsAt: z.string().datetime(), endsAt: z.string().datetime(), noGoWindows: z.array(z.object({start: z.string(), end: z.string(), reason: z.string()}))}),
  contacts: z.array(z.object({role: z.string(), name: z.string(), channel: z.string()})),
  authorizingParty: z.object({oidcSub: z.string(), webAuthnCredId: z.string()}),
  signature: z.object({alg: z.literal('ES256'), jws: z.string(), signedAt: z.string().datetime()}),
  ledgerAnchor: z.object({merkleRoot: z.string(), tsaToken: z.string()}).optional()
});
```

### 4.2 Authorization gate (Rego)

Every MCP tool call goes through OPA before execution. Reject the diff if Copilot bypasses this.

```rego
# packages/policy-engine/rules/authorize.rego
package avs.authorize

default allow = false

allow {
    input.target.cidr_in_scope
    not input.target.cidr_excluded
    input.tool_category in input.roe.test_categories
    input.action_destructive == false
    input.now >= input.roe.starts_at
    input.now <= input.roe.ends_at
    not in_no_go_window
}

allow {
    input.target.cidr_in_scope
    not input.target.cidr_excluded
    input.action_destructive == true
    some i
    input.roe.destructive_opt_ins[i].asset == input.target.id
    input.roe.destructive_opt_ins[i].allow == true
}

deny[reason] {
    not allow
    reason := build_deny_reason(input)
}
```

Rego must be unit-tested in `tests/policy/`. Copilot must include: in-scope ✓, in-exclusion ✗, destructive without opt-in ✗, destructive with opt-in ✓, time-window before ✗, time-window after ✗, no-go window ✗.

### 4.3 RoE signing flow (UI: `02-scope.html`)

- The signer touches a YubiKey / Windows Hello via WebAuthn.
- The browser signs a JWS over `{scope_hash, tools_allowed, destructive_optins, iat, exp}` using ES256 and the WebAuthn credential.
- Server verifies the JWS, hashes the full RoE, and **anchors the hash to the evidence ledger** (Merkle leaf + RFC 3161 TSA token).
- A scan cannot start unless `RoE.ledgerAnchor` is set.

---

## 5. Evidence ledger (ADR-4)

### 5.1 Storage

- PostgreSQL 16 table `evidence`:
  ```sql
  CREATE TABLE evidence (
    idx           BIGSERIAL PRIMARY KEY,
    scan_id       UUID NOT NULL,
    actor         TEXT NOT NULL,        -- e.g. 'recon-agent', 'orchestrator'
    action        TEXT NOT NULL,        -- e.g. 'mcp.nmap.scan'
    payload_hash  BYTEA NOT NULL,       -- sha256 of canonicalized payload
    payload_blob  TEXT,                 -- redacted JSON (PDPA-safe)
    parent_hash   BYTEA NOT NULL,       -- previous row's leaf_hash
    leaf_hash     BYTEA NOT NULL,       -- sha256(parent_hash || payload_hash)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(scan_id, idx)
  );
  CREATE TABLE ledger_anchor (
    scan_id    UUID PRIMARY KEY,
    merkle_root BYTEA NOT NULL,
    tsa_token  BYTEA NOT NULL,
    anchored_at TIMESTAMPTZ NOT NULL
  );
  ```
- The table is **append-only**: revoke `UPDATE` and `DELETE` for the application role.
- Periodically (every N rows or T seconds) compute the Merkle root over `leaf_hash` and submit to an RFC 3161 TSA. Store the TSA token in `ledger_anchor`.

### 5.2 Auto-redaction (PDPA)

- Before writing `payload_blob`, run through `packages/shared-schemas/redact.ts`:
  - Thai citizen ID: `\b\d{1}-\d{4}-\d{5}-\d{2}-\d{1}\b` → `[CID-REDACTED]`
  - Thai phone: `\b0\d{1,2}-?\d{3}-?\d{4}\b` → `[PHONE-REDACTED]`
  - Banking acct: bank-prefix + 9-12 digits patterns → `[ACCT-REDACTED]`
- Tests must cover the regex edge cases. False negatives are a SEV-1 defect.

---

## 6. Sandboxing (ADR-3 / ADR-6)

### 6.1 Tool execution boundary

- **All MCP tool invocations** run inside a sandbox:
  - Default: Firecracker microVM with rootfs cloned from a pinned image.
  - Fallback: gVisor (`runsc`) on non-KVM clusters.
- Egress from the sandbox is deny-by-default; only the target subnet (per RoE) and the ledger ingestion endpoint are allowed.
- Each sandbox run produces:
  - stdout/stderr (captured, hashed, anchored)
  - artifacts directory (mounted into ledger writer)
  - exit code
- Sandbox lifetime is bounded (default 5 minutes). Timeouts are policy denies.

### 6.2 Destructive-by-default = NO (ADR-6)

- The Vuln agent **never** runs a destructive payload against the live target.
- Confirming "exploitable" is a two-step:
  1. Capture *evidence* of the precondition (e.g., SSRF callback hits AVS canary).
  2. Replay the chain in a Firecracker clone of the target's image (cloud images snapshot, on-prem: customer-supplied AMI/image).
- If Copilot generates a path that calls a destructive payload against the live target, **reject the diff.**

---

## 7. Scoring stack (ADR-5)

`packages/shared-schemas/score.ts` produces `chainScore = f(cvss40, epss, kev, ssvc, reachability)`:

```ts
// Pseudocode — must be reviewed by a security engineer before tuning weights.
function chainScore(c: Chain): number {
  const baseSev = max(c.findings.map(f => f.cvss40));            // 0-10
  const epssBoost = avg(c.findings.map(f => f.epss));            // 0-1
  const kevBoost = c.findings.some(f => f.inKEV) ? 1 : 0;        // 0 or 1
  const ssvcRank = c.ssvcDecision === 'act' ? 1 : c.ssvcDecision === 'attend' ? 0.5 : 0;
  const reach = c.graphReachability;                             // 0-1
  return clamp(0, 100,
    10 * baseSev +
    15 * epssBoost +
    10 * kevBoost +
    10 * ssvcRank +
    25 * reach
  );
}
```

Refresh sources daily:
- NVD JSON feed for CVE + CVSS 4.0
- CISA KEV catalog
- FIRST EPSS daily CSV
- SSVC decisions: per-asset, computed from environment metadata

---

## 8. MCP tools to wrap (Phase 2 v0.1 set)

| Server | Tool | Output | Destructive? |
|--------|------|--------|--------------|
| nmap-mcp | `mcp.nmap.scan(target, ports, scripts)` | XML + parsed JSON | No |
| masscan-mcp | `mcp.masscan.sweep(cidr, rate)` | JSON | No |
| dns-mcp | `mcp.dns.resolve(name, types)` | JSON | No |
| ct-mcp | `mcp.cert-transparency.lookup(domain)` | JSON | No |
| nuclei-mcp | `mcp.nuclei.run(target, templates)` | JSON | No (templates pinned) |
| trivy-mcp | `mcp.trivy.image(ref)` / `mcp.trivy.fs(path)` | JSON | No |
| grype-mcp | `mcp.grype.scan(ref)` | JSON | No |
| syft-mcp | `mcp.syft.sbom(ref)` | CycloneDX JSON | No |
| zap-mcp | `mcp.zap.activeScan(target, profile)` | JSON | Possibly (gated) |
| prowler-mcp | `mcp.prowler.aws(account)` | JSON | No (read) |
| scoutsuite-mcp | `mcp.scoutsuite.run(provider, account)` | JSON | No (read) |
| bloodhound-mcp | `mcp.bloodhound.collect(domain)` | JSON | No |
| inspector-mcp | `mcp.aws.inspector(account)` | JSON | No |
| defender-mcp | `mcp.defender.findings(sub)` | JSON | No |
| gcp-scc-mcp | `mcp.gcp.scc.findings(project)` | JSON | No |
| sandbox-mcp | `sandbox.firecracker.replay(image, payload)` | JSON | Yes (in sandbox only) |

Each MCP server exposes:
- `health` endpoint
- `metadata` (tools, params, schemas)
- `invoke` (with structured request/response)
- OTel hooks

---

## 9. UI — implement these screens in this order

The polished HTML mockups in `04-ux-package/mockups/` are the visual contract. React components must match the layout/tokens.

| Order | Screen | File | Notes |
|-------|--------|------|-------|
| 1 | RoE editor | `02-scope.html` | Hardest; build the WebAuthn signing flow first end-to-end. |
| 2 | Live timeline | `03-live-timeline.html` | Streams events via Server-Sent Events from `apps/api`. |
| 3 | Findings list | `04-findings.html` | Filter rail driven by query params; cards lazy-load evidence. |
| 4 | Chain detail | `05-chain-detail.html` | Graph visualization (Cytoscape.js or D3). |
| 5 | Dashboard | `01-dashboard.html` | Aggregates from Postgres + Neo4j. |
| 6 | Reports | `06-report.html` | PDF generation via Puppeteer; sign + anchor bundle. |
| 7 | Settings | `07-settings.html` | Model router config; tenant CRD. |

**Bilingual contract:** every user-facing string lives in `packages/i18n/{en,th}.json`. The build runs `i18n-lint` which fails CI if any string is present in EN but missing in TH (or vice versa). The `t()` helper in React components is the only allowed source of user text.

Use Tailwind tokens defined to match `brand/ci-guide.md`:
```js
// tailwind.config.ts
extend: {
  colors: {
    'avs-ink': '#0B1220', 'avs-paper': '#F7F9FC',
    'avs-shield': '#1F6FEB', 'avs-pulse': '#22D3EE',
    'sev-critical': '#DC2626', 'sev-high': '#EA580C',
    'sev-medium': '#D97706', 'sev-low': '#65A30D', 'sev-info': '#0EA5E9'
  },
  fontFamily: {
    sans: ['Inter', 'Sarabun', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Cascadia Mono', 'ui-monospace', 'monospace']
  }
}
```

---

## 10. Public API (selected endpoints)

```
POST   /api/v1/scopes                Create RoE (draft)
POST   /api/v1/scopes/:id/sign       Submit JWS, anchor to ledger
POST   /api/v1/scans                 Start scan against signed RoE
GET    /api/v1/scans/:id             Scan status
GET    /api/v1/scans/:id/events      SSE stream of agent events
GET    /api/v1/scans/:id/findings    Paginated findings
GET    /api/v1/findings/:id          Finding detail + evidence refs
GET    /api/v1/chains/:id            Chain detail (graph + steps)
POST   /api/v1/reports/:scanId       Build report, returns signed bundle URL
GET    /api/v1/evidence/:idx         Single evidence row + Merkle proof
```

All endpoints require an OIDC bearer token. Mutations require step-up (WebAuthn) for the RoE-signing endpoint.

---

## 11. Observability

- **Traces:** every agent call, every MCP invocation, every OPA decision is a span. Root span = scan-id. Export via OTLP to customer's collector.
- **Metrics (Prometheus-compatible):**
  - `avs_findings_total{severity,source}`
  - `avs_chains_validated_total`
  - `avs_fp_suppressed_total`
  - `avs_authorization_denials_total{reason}`  ← **must remain at 0 except for tests**
  - `avs_llm_call_duration_seconds{role,provider,model}`
- **Logs:** structured JSON; sensitive payloads pass through redactor before logging.

---

## 12. Build, test, ship

### 12.1 CI

```yaml
# .github/workflows/ci.yml (sketch)
jobs:
  lint:           [eslint, ruff, golangci-lint, tsc --noEmit, i18n-lint]
  test-unit:     [vitest, pytest, go test]
  test-policy:   [opa test ./packages/policy-engine/...]
  test-safety:   [agentdojo replay against orchestrator stub]
  test-e2e:      [playwright against k3d cluster + mocked LLMs]
  build:         [docker buildx, push to ghcr.io/<org>/avs-*]
  scan:          [trivy + grype + syft, fail on critical]
  sign:          [cosign sign --yes <image>]
```

### 12.2 Required tests Copilot must generate

- Authorization gate: 100% Rego rule coverage; mutation testing.
- Redaction: at least 30 Thai PII fixtures (citizen ID, phone, account formats).
- Critic isolation: assert no `orchestrator_history` keys appear in Critic prompt.
- Sandbox boundary: assert MCP calls outside the sandbox fail closed.
- Bilingual: `i18n-lint` blocks CI if EN/TH parity breaks.
- Replay determinism: given fixed seeds + recorded evidence, scoring output is byte-stable.

### 12.3 Done-definition for v0.1

- [ ] All 7 UI screens render and are bilingual.
- [ ] A signed RoE survives a round-trip through ledger + reload.
- [ ] An end-to-end scan against the supplied test target produces ≥ 1 critical chain with 4+ evidence rows, anchored.
- [ ] OPA denies all 12 negative test cases.
- [ ] FP rate on the 50-item benchmark set ≤ 5% (Critic enabled).
- [ ] No call paths bypass the sandbox.
- [ ] Bundle export is verifiable: external verifier can re-compute the Merkle root and validate the TSA token.

---

## 13. Anti-patterns (Copilot, do not generate these)

- ❌ "Just call the MCP tool directly without OPA — speeds up dev." → **No. OPA is on the hot path.**
- ❌ "Run the destructive payload against the live target if confidence is high." → **Never. Sandbox or evidence-only.**
- ❌ "Share the orchestrator context with the Critic to give it more info." → **Defeats the corroboration property.**
- ❌ "Skip TH translation; just ship EN, we'll add Thai later." → **Bilingual is build-time enforced.**
- ❌ "Use a single LLM provider; multi-vendor adds complexity." → **ADR-2 is binding.**
- ❌ "Store payloads unredacted; we'll filter on read." → **PDPA violation. Redact before write.**
- ❌ "Use `git push --force` on `main` to clean up." → **Refuse.**

---

## 14. Reference: prior art Copilot can study

- **PentestGPT** (USENIX 2024) — multi-agent reasoning approach.
- **Google Big Sleep** — found CVE-2025-6965 (SQLite) in July 2025 via agentic discovery.
- **MITRE Caldera with MCP plugin** — adversary emulation as MCP server.
- **AgentDojo** — adversarial benchmark suite for prompt injection / tool misuse.
- **MCP donation to Linux Foundation** (Dec 2025) — standardize on the Foundation's reference SDK.
- **OWASP LLM Top 10 (2025)** — controls catalog for LLM-app risks.
- **NIST AI 600-1** — gen-AI risk profile.

Citations are in `research-competitive.md` and `research-technical.md`.

---

## 15. Hand-off checklist

When Copilot says "Phase 2 v0.1 done", verify:

- [ ] `apps/orchestrator` boots, accepts a signed RoE, schedules agent tasks.
- [ ] `apps/agent-runner` runs in K8s, hosts ≥ 5 MCP servers from the §8 list.
- [ ] `apps/ledger` writes append-only rows, computes Merkle, anchors via TSA.
- [ ] `apps/web` serves all 7 screens, both languages.
- [ ] `tests/policy` ≥ 95% line coverage; **all tests green**.
- [ ] `tests/safety` (AgentDojo subset) **all tests green**.
- [ ] CI signs the image, scans dependencies, generates SBOM.
- [ ] Helm chart deploys to a k3d cluster end-to-end.
- [ ] One demo video: load RoE → sign → scan → chain → report.

This is the Phase 2 acceptance gate. Until every box is checked, v0.1 is not shipped.
