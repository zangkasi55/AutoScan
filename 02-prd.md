# 02 — Product Requirements Document (PRD)

**Product:** Agentic Vulnerability Scanner (AVS) — codename *Sentry-AI*
**Version:** v0.1 (Phase 1 — research + design)
**Owner:** PM, one-man-company orchestrator
**Date:** 2026-04-30 (Asia/Bangkok)
**Out of scope (this PRD):** pricing, costing, financial modeling, marketing, GTM. Per user clarification 2026-04-30.

---

## 1. Problem Statement

Thai enterprise and MSSP security teams are buying CVE coverage from global scanners (Tenable / Qualys / Rapid7) and chained-attack validation from autonomous-pentest platforms (Pentera / Horizon3 / XBOW), but face four unsolved gaps:

1. CVE-only scanners produce 5,000-finding lists no one can triage; chain-validation platforms don't speak Thai or align to PDPA evidence requirements.
2. False-positive overload + the "AI slop" reputational risk — agentic tools that flood maintainers with bogus findings are net-negative.
3. Compliance scans (PCI ASV, BoT pentest cadence, NCSA-CII reporting) require timestamped, hash-anchored evidence packages no global vendor produces in Thai-aligned form.
4. Authorization scope and rules-of-engagement (RoE) are buried in Word documents, not enforced as a runtime constraint on the scanning tool itself.

## 2. Vision

An autonomous, multi-LLM scanner that produces **fewer, better-evidenced, exploit-chain-aware findings**, in **Thai and English**, with **PDPA-native chain-of-custody** and a **runtime-enforced authorization gate** — so a CISO can hand a regulator a single signed evidence pack and a remediation owner can fix the actual cause without a translator.

## 3. Target Users (Personas)

### Persona 1 — "Khun Pim", Internal Vulnerability-Management Lead at a Thai bank
- Reports to the CISO; owns BoT cyber-resilience scan cadence and PCI ASV.
- Has 3 analysts, ~15,000 assets across on-prem + AWS + Azure.
- Pain: 5,000-finding monthly Nessus reports; her team can only realistically remediate ~120/month.
- Wants: "Show me the 50 findings that actually let an attacker into the core banking environment, with proof, in a format I can give to BoT."

### Persona 2 — "Khun Aek", MSSP technical lead at a Thai SI
- Sells managed VM + pentest services to mid-market customers.
- Currently resells Qualys; differentiates on Thai-language reports and on-site analysts.
- Pain: every customer report is hand-translated; pentest cadence is once-a-year, customers want quarterly.
- Wants: a multi-tenant scanner that produces Thai/EN reports with his agency's branding and supports continuous validation cadence.

### Persona 3 — "Khun Wit", Internal Red-Team Lead at a Thai telco
- 4-person red team; runs purple-team exercises with the SOC quarterly.
- Pain: spends 60% of engagement time on recon/scope/setup; only 40% on real attacker reasoning.
- Wants: an agent that does the "scan + chain + suggest paths" busywork so his team focuses on novel attacks.

## 4. Product Principles

1. **Evidence-first.** No claim ships without (a) a deterministic-tool signal, (b) an LLM-corroborated interpretation, (c) a hashed evidence artifact in the chain-of-custody store.
2. **Authorization is a runtime constraint, not a checkbox.** The agent reads the signed RoE on every step and aborts on scope deviation.
3. **Bilingual by default.** Every customer-facing surface ships Thai and English from day one.
4. **Plan, don't pwn.** The LLM never executes destructive payloads. Destructive checks (auth-cracking, exploit verification with side effects) are gated behind explicit per-asset opt-in.
5. **Composition over re-implementation.** Wrap deterministic scanners (Nuclei / Nmap / Trivy / ZAP / Prowler / BloodHound CE) via MCP; do not rebuild them.
6. **Multi-vendor model diversity.** Claude Opus 4.7 orchestrator + GPT-5.5 specialist agents; routing decisions are observable and replaceable.
7. **PDPA-native.** Every artifact has a retention policy, encryption, and access trail; personal data captured incidentally is auto-redacted before storage.

## 5. MVP Capabilities (v0.1)

### 5.1 Authorization & Scope (the foundation)
- **Rules of Engagement (RoE) document** — structured object: scope (CIDRs, domains, cloud accounts), exclusion list, allowed test types, contact tree, time window, destructive-check opt-ins per asset, signature block.
- **RoE signature gate** — scan cannot start until digitally signed by an authorized contact (verified via SSO + step-up MFA).
- **Continuous scope enforcement** — every tool invocation passes through an RoE-aware policy engine; out-of-scope target → hard-fail + audit log entry.
- **Auto-pause on anomaly** — if the agent's planned next step would touch a non-listed target, agent pauses and prompts the analyst.

### 5.2 Asset Discovery & Inventory
- **Surfaces:** IPv4/IPv6 ranges, domains/subdomains, AWS / Azure / GCP accounts, Kubernetes clusters, Active Directory / Entra ID, container registries.
- **Tools wrapped (MCP):** Nmap, Masscan, ProjectDiscovery (Subfinder, httpx), AzureHound, SharpHound, Prowler, ScoutSuite, Trivy (filesystem/IaC), Syft.
- **Output:** unified Asset Graph with parent/child relationships, tags, and ownership. Stored as graph (Neo4j or PG with `pgRouting`) for chain reasoning.

### 5.3 Vulnerability Detection
- **Tools wrapped:** Nuclei (templates), Trivy + Grype (SCA + container), OWASP ZAP Automation Framework (web/API), AWS Inspector v2 / Defender for Cloud / GCP SCC findings ingestion (no double-scan), BloodHound CE for AD/Entra path analysis.
- **Coverage targets for v0.1:** Network/host CVEs, web/API OWASP Top 10, container/IaC misconfigurations, multi-cloud misconfigurations, AD/Entra attack paths.
- **Out for v0.1 (roadmap):** AI/LLM application probes (MITRE ATLAS), dynamic mobile app testing, OT/SCADA.

### 5.4 Exploit-Chain Reasoning
- **Planner (Claude Opus)** consumes Asset Graph + raw findings + EPSS/KEV/SSVC enrichment.
- **Specialist sub-agents (GPT-5.5)** corroborate each "high"/"critical" finding via at least 2 independent signals (banner + behavior + auth response, etc.) before promotion.
- **Chains** are produced as ordered traversals of the Asset Graph: e.g., `internet-facing API → SSRF → metadata service → IAM credential → assume-role → RDS read`.
- **Evidence-only by default.** Reasoning, not execution. Destructive verification is per-asset opt-in only.

### 5.5 Prioritization
- Scoring stack: **CVSS 4.0 (base + threat + environmental) + EPSS probability + CISA KEV flag + SSVC decision tree + chain reachability score**.
- One headline number per finding (0–100), a sub-score breakdown, and a one-sentence "why this is N" explanation generated by the report writer.

### 5.6 Reporting (THE differentiator)
- **Three audiences, three views, all bilingual:**
  - **CISO summary** — 1-page exec brief, attack-path narrative, top-10 chains, regulator alignment.
  - **Analyst view** — full finding list, filterable, with reproduction steps and evidence hashes.
  - **Owner ticket** — Jira/ServiceNow-ready, per-finding remediation with code snippets and patch links.
- **Formats:** HTML (interactive), PDF (signed), CSV/Excel (raw findings), STIX/CycloneDX (interop).
- **Languages:** Thai and English mirrored; analysts can switch without losing state. Translation of vendor-supplied advisory text is reviewed by the critic agent (no raw-MT output).
- **Regulator pack:** pre-formatted PDPA / BoT / PCI / NCSA-CII evidence bundles with hash manifest.

### 5.7 Continuous Validation Cadence
- Configurable schedules (PCI quarterly, BoT annual, on-change, on-deploy webhook).
- Diff between runs surfaces *new* findings vs *recurring* vs *resolved*; SLA timers per finding.

### 5.8 Chain-of-Custody (PDPA core)
- **Evidence ledger** — append-only, hash-chained store of every scan artifact (request/response, screenshot, parsed output, agent reasoning trace).
- **Auto-redaction** — any payload that triggers PII detectors (Thai citizen ID, phone, email, address, banking number formats) is redacted before storage; unredacted source is sealed in customer-controlled HSM-backed encryption.
- **Access trail** — every read of an evidence record is logged; analysts authenticate via SSO + per-tenant role.
- **Retention** — per-tenant policy aligned with PDPA breach-evidence requirements; hard-delete on policy boundary with cryptographic erase.

### 5.9 Operator UX
- Web app (primary). CLI (secondary) for CI/CD integration. API (REST + webhook) for embedding.
- Real-time scan timeline (agent-by-agent activity, MCP tool invocations).
- Pause / resume / abort scan controls.
- "What is the agent doing right now?" panel — every reasoning step visible to the analyst (auditability).

## 6. Non-Goals (v0.1)

- **No autonomous exploitation that causes side effects** — verification of exploitability must be evidence-only by default.
- **No replacement for manual pentest engagement** — AVS augments, does not pretend to replace, expert humans on novel work.
- **No bug-bounty submission automation** — explicitly anti-pattern (the "AI slop" failure mode).
- **No code-fix authorship** — AVS suggests fixes, never commits to customer repos.
- **No pricing / licensing model** in this document — out of scope per user.
- **No multi-tenant SaaS hosting commitment** in v0.1 — single-tenant on-prem / private cloud is the v0.1 deployment shape; SaaS is roadmap.

## 7. User Stories (selected — full set in `04-ux-package/journey.md`)

### 7.1 Onboarding
- *As Khun Pim, I want to upload our scope document and have AVS extract a structured RoE, so I can review and sign it before any scan starts.*
- *As Khun Aek, I want to provision a tenant per customer and brand the report templates, so customers see my agency's identity.*

### 7.2 Scanning
- *As Khun Wit, I want to start a scan with a one-line command (`avs scan <RoE-id>`) so I can integrate AVS into our purple-team runbook.*
- *As Khun Pim, I want to watch the agent timeline in real time so I can audit what is being executed against our network.*

### 7.3 Findings
- *As Khun Pim, I want to see the top 10 attack chains, not the top 5,000 findings, so I can brief the CISO in 5 minutes.*
- *As an analyst, I want to expand any chain into its constituent findings with hashed evidence so I can reproduce or dispute.*

### 7.4 Remediation
- *As an analyst, I want to push tickets to Jira with localized Thai descriptions and English commit-message guidance, so internal engineers can act without re-translation.*

### 7.5 Compliance
- *As Khun Pim, I want a pre-formatted BoT 30-day-incident evidence bundle generated from a finding, with SHA-256 hashes anchored to a public timestamp service, so I can give it to the regulator unmodified.*

### 7.6 Safety
- *As an analyst, I want the scanner to pause and ask me before any test that could cause side effects, so I never accidentally take down production.*
- *As a CISO, I want every scope deviation logged and emailed to me in real time, so I have an audit trail.*

## 8. Success Criteria (v0.1)

| Metric | Target | Measurement |
|---|---|---|
| **False-positive rate** on critical/high findings | ≤ 5% | Customer-acknowledged FPs ÷ total critical/high findings |
| **Chain coverage** | ≥ 3 distinct chains surfaced per 1,000 findings | Per-scan attack-chain density |
| **Time from scope-signed → first finding** | ≤ 30 minutes for /24 scope | E2E scan timer |
| **Bilingual coverage** | 100% of customer-facing strings | Lint job in CI |
| **PDPA evidence completeness** | 100% of findings have hash + redaction record + access trail | Evidence-ledger audit |
| **Authorization-gate violations** | 0 (hard requirement) | Audit log |
| **Tooling crash rate** | < 1% of MCP calls | MCP server telemetry |

## 9. Safety, Ethics, and Compliance Requirements (binding)

1. **Hard refusal.** Scanner refuses to start without signed RoE; no override, no "demo mode" backdoor.
2. **Scope continuous enforcement** at every tool invocation.
3. **Destructive checks** disabled by default; per-asset opt-in only; depth caps; full audit log.
4. **Auto-redaction** of personal data in stored evidence.
5. **Encryption** at rest (AES-256-GCM, customer-controlled keys) and in transit (TLS 1.3).
6. **Access control** — RBAC, SSO via OIDC/SAML, step-up MFA for destructive actions.
7. **OWASP LLM Top 10 (2025)** controls inside agent loop — prompt-injection defenses, output validation, no over-agentic behaviors (LLM06).
8. **NIST AI RMF** alignment at the program layer; documented governance for model upgrades.
9. **Sandbox isolation** of every tool call (gVisor / Firecracker microVM).
10. **Kill switch** — operator-accessible button that aborts all running agents within 5 seconds.
11. **No cross-tenant data flow** ever.
12. **Model-call logging** — prompts, responses, tool calls retained per RoE (typically 90–365 days) for audit.

## 10. Open Issues / Decisions Needed

| # | Issue | Owner | Status |
|---|---|---|---|
| O-1 | Single-tenant deployment shape (on-prem container vs Kubernetes Helm vs Azure managed app) | Architect | Decide in `05-architecture.md` |
| O-2 | Evidence ledger backing store (append-only PG + Merkle vs purpose-built like Quorum) | Architect | Decide in `05-architecture.md` |
| O-3 | Whether to ship AI/LLM-app probes (MITRE ATLAS) in v0.1 or v1.1 | PM | **Decision: v1.1 roadmap.** Out of v0.1. |
| O-4 | Burp Suite license model (community vs enterprise REST API) | Legal/PM | Defer to roadmap; v0.1 ships ZAP only |
| O-5 | Hosted vs on-prem-only for v0.1 | PM | **Decision: on-prem / customer-cloud only for v0.1**. SaaS deferred. |

## 11. Phase 1 → Phase 2 Handoff

This PRD plus `05-architecture.md`, `04-ux-package/`, the HTML mockups, and the GitHub Copilot build spec (`final/github-copilot-build-spec.md`) constitute the inputs for Phase 2 (developer build). No code is committed in Phase 1.
