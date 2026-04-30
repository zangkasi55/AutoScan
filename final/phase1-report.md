# Phase 1 Report — Agentic Vulnerability Scanner (AVS)

**Codename:** Sentry-AI · **Tagline:** *Autonomous defenders. Verifiable proof.* / *เอเจนต์ไซเบอร์อัตโนมัติ. หลักฐานพิสูจน์ได้.*
**Phase:** 1 · Validate (no production code)
**Run:** 2026-04-30
**Owner:** danait@microsoft.com · **Manager:** Vilaiporn Taweelappontong

---

## 1. Executive summary

AVS is an on-prem / customer-cloud **agentic vulnerability scanner** that pairs a Claude Opus 4.7 orchestrator with a fleet of GPT-5.5 specialist agents (recon, vuln, exploit-reasoning, critic, report-writer) to autonomously discover, validate, and explain attack chains across customer infrastructure.

The Phase 1 thesis: **today's vulnerability scanners produce overwhelming finding lists with high false-positive rates and weak attack-path narratives. Existing AI-pentest tools (XBOW, Pentera, Horizon3.ai NodeZero) are pure SaaS, scarcely localized for Thailand, and don't carry the chain-of-custody an enterprise auditor or the Bank of Thailand will recognize.**

AVS attacks four wedges that are differentiated for the Thailand market:

1. **Exploitability-first findings** — every promoted finding is independently re-derived by a Critic agent before it surfaces. Target FP rate ≤ 5% (vs industry-typical 20-30%).
2. **PDPA-native chain-of-custody** — Merkle-chained, RFC 3161 timestamped evidence ledger; auto-redaction of Thai PII; DPO co-sign for regulator exports.
3. **Authorization is a product feature** — RoE is a signed, hash-anchored artifact; every MCP tool call is OPA-gated against it at runtime, not just on paper.
4. **Continuous-validation cadence** — designed to run weekly against in-scope perimeters, generating PCI / BoT / NCSA-CII evidence packs by default.

Phase 1 deliverables — research, PRD, brand identity, architecture (8 ADRs), full UX package with 7 polished HTML mockups, test pass, GitHub Copilot build spec — are complete. **No production code yet, by design.**

---

## 2. What was built in Phase 1

| Artifact | Location | Purpose |
|----------|----------|---------|
| Brief | `00-brief.md` | Original intent + explicit exclusions (no pricing, no GTM). |
| Competitive landscape research | `research-competitive.md` (35 sources) | Gap analysis vs Tenable, Qualys, Rapid7, Pentera, Horizon3.ai NodeZero, XBOW, Mindgard, RunSybil. |
| Technical research | `research-technical.md` | Orchestration patterns, MCP, sandbox primitives, scoring stack. |
| Market research consolidation | `01-market-research.md` | Concept scoring rubric → A+B+C+F selected as MVP wedges. |
| PRD | `02-prd.md` | 3 personas, 7 product principles, 9 capability sections, 12 binding safety/compliance requirements. |
| Brand identity | `brand/ci-guide.md` + `brand/logo.svg` + `brand/logo-mark.svg` | Palette, typography, voice, logo. |
| Architecture | `05-architecture.md` | 8 ADRs · MCP substrate · multi-vendor LLMs · sandbox-every-tool · append-only Merkle ledger · scoring stack · evidence-only-by-default · on-prem v0.1 · bilingual contract. |
| UX journey | `04-ux-package/journey.md` | 8 stages + dark paths. |
| Wireframes | `04-ux-package/wireframes.md` | W1–W7. |
| Polished HTML mockups | `04-ux-package/mockups/00–07.html` + shared `assets/styles.css` | Full UI design covering all key flows in EN+TH. |
| Test report | `07-test-report.md` | 0 SEV-1 issues. |
| Known gaps | `known-gaps.md` | 10 tracked items, owners assigned. |
| **GitHub Copilot build spec** | `final/github-copilot-build-spec.md` | The Phase 2 source-of-truth. |

---

## 3. Concept scoring (PM rubric → MVP wedges)

The PM weighed 12 candidate differentiators against 4 criteria: customer pull (Thailand), technical feasibility, defensibility, and time-to-evidence. Top 4 picked for MVP:

| Wedge | Customer pull | Defensibility | Why it's in v0.1 |
|-------|---------------|---------------|------------------|
| **A — Exploitability-first reporting** | High (every CISO complains about FP noise) | Medium (Critic agent + scoring stack is non-trivial) | The single most-asked feature; immediate demo value. |
| **B — PDPA-native evidence ledger** | High (BoT-regulated banks, Thai gov MSSPs, NCSA-CII reporters) | High (operational moat: redaction + ledger + TSA + DPO co-sign is hard to copy) | Localized advantage XBOW/Pentera don't have. |
| **C — FP-suppression metric as a product KPI** | Medium-High | Medium | Cheap to instrument, drives every release decision. |
| **F — Continuous-validation cadence** | High (PCI quarterly, BoT annual, attacker-driven changes) | Medium | Aligns with the regulator calendar in TH. |

Out of v0.1: SaaS hosting, AI/LLM-app probing (deferred to v1.1), pricing/marketing (per user direction).

---

## 4. Architecture in one paragraph

A Node.js 22 + Fastify **orchestrator** decomposes a signed Rules-of-Engagement document into agent tasks. Five Python 3.12 specialist agents (Recon / Vuln / Exploit-Reasoning / Critic / Report-Writer) call MCP-wrapped security tools (Nmap, Nuclei, Trivy, ZAP, Prowler, ScoutSuite, BloodHound CE, etc.) inside Firecracker microVM sandboxes. Every tool call is gated by an OPA / Rego policy that re-validates against the RoE hash. Every output is written append-only to a PostgreSQL evidence ledger; row hashes are Merkle-chained and the root is RFC-3161 anchored. Findings are scored with CVSS 4.0 + EPSS + CISA KEV + SSVC + graph reachability (Neo4j). The Critic re-derives every promoted finding using an *independent* model + clean context (no shared history) to suppress false positives. A React 19 + Vite + Tailwind v4 web UI surfaces 7 screens — RoE editor, dashboard, live timeline, findings, chain detail, reports, settings — entirely bilingual EN+TH at build time.

ADRs locked in:
1. **MCP** as the agent-tool substrate (donated to Linux Foundation Dec 2025; long-term standard).
2. **Multi-vendor LLM** (Anthropic + OpenAI) for cross-provider failover and role specialization.
3. **Sandbox every tool** (Firecracker primary, gVisor fallback).
4. **Append-only Merkle ledger + RFC 3161 TSA**.
5. **Scoring = CVSS 4.0 + EPSS + KEV + SSVC + reachability**.
6. **Destructive checks evidence-only by default**; explicit per-asset opt-in required to escalate.
7. **On-prem / customer-cloud only in v0.1**; SaaS is post-Phase 3.
8. **Bilingual is a build-time contract** (`i18n-lint` blocks CI on EN-only or TH-only strings).

---

## 5. UX in one screen

The mockup index at `04-ux-package/mockups/00-index.html` links the seven screens. Highlights:

- **02-scope.html** — RoE editor with structured scope/exclusions, time window, destructive opt-ins, JWS preview, WebAuthn signing, and visible ledger anchor. Authorization is shown as a product feature, not a checkbox.
- **03-live-timeline.html** — six swim-lanes (Orchestrator + 5 specialists) showing every MCP tool call, every policy decision, and every evidence chip in real time. A policy-stop event is visualized when the recon agent attempts an excluded host (203.144.128.42 — the legacy mainframe).
- **04-findings.html** — top-chains-first; bilingual cards with CVSS / EPSS / KEV / SSVC chips and one-click push-to-Jira.
- **05-chain-detail.html** — graph visualization of the SSRF→IMDS→IAM→S3-PII chain, bilingual narrative, per-step evidence (including Firecracker sandbox replay output), audit trail with ledger anchors.
- **06-report.html** — audience picker (CISO / analyst / asset owner / regulator), signed bundle with verifiable Merkle root, regulator pack assembly for PDPA / BoT / PCI / NCSA-CII.
- **07-settings.html** — model router (per-role primary + fallback), token usage telemetry, security policies, audit & retention.

Brand tokens (`--avs-shield #1F6FEB`, `--avs-pulse #22D3EE`, severity scale, Inter + Sarabun typography) are shared across every screen via `assets/styles.css`.

---

## 6. Test pass — verdict

`07-test-report.md` covers PRD-vs-research traceability, architecture-vs-PRD coverage, and a functional walk of all 7 mockups. Every safety-critical control (authorization gate, sandbox boundary, evidence ledger, PDPA redaction, DPO co-sign, OWASP LLM Top 10) is visibly represented.

- **Severity 1 (blockers): 0**
- **Severity 2 (should-fix): 2** (both tracked, neither blocks the Phase 2 build).
- **Severity 3 (notes for Phase 2): 4** (i18n-lint, Critic isolation runtime check, OTel wiring, destructive-opt-in state machine).

Phase 1 design package is internally consistent, traceable, and ready to drive Phase 2.

---

## 7. The build spec

`final/github-copilot-build-spec.md` is the authoritative document for Phase 2. It compresses the PRD, architecture, and UX into a build-runnable plan: exact tech versions, repo layout, multi-LLM agent contracts, the Critic isolation rule, RoE schema, OPA gate Rego, evidence-ledger DDL, sandboxing rules, MCP tool catalog, UI screen order, public API endpoints, observability spec, CI pipeline, required tests, done-definition checklist, and 7 anti-patterns Copilot must not generate.

This is the file to hand to GitHub Copilot to build the MVP.

---

## 8. What is intentionally NOT in Phase 1

Per user direction:
- No pricing, no costing, no marketing, no GTM.
- No production code (deferred to Phase 2).
- No SaaS hosting plan (out of scope for v0.1).
- No AI/LLM-app probing capability (deferred to v1.1).

These are recorded as deliberate exclusions, not gaps.

---

## 9. Recommended next steps

1. **Hand the build spec to GitHub Copilot** to scaffold `avs/` with the §1 layout, then implement the §9 UI screens in the listed order. The hardest path (RoE editor → WebAuthn signing → ledger anchor) should ship end-to-end first.
2. **Pin the Phase 2 acceptance gate** to the §15 checklist in the build spec. Treat the FP-rate target (≤5% on the 50-item benchmark) and the authorization-denial counter (must remain at 0 except in tests) as merge-blockers.
3. **Stand up the AgentDojo subset** as a CI safety harness before agent code goes live.
4. **Pre-source a Thai design partner** (one BoT-regulated bank or one MSSP) to dry-run the v0.1 UX once it boots — they will catch what mockups can't.

---

## 10. File index (Phase 1 deliverables)

```
omc-agentic-vuln-scanner/
├── 00-brief.md
├── phase-status.md
├── research-competitive.md         (35 cited sources)
├── research-technical.md
├── 01-market-research.md
├── 02-prd.md
├── 05-architecture.md              (8 ADRs)
├── 07-test-report.md
├── known-gaps.md
├── brand/
│   ├── ci-guide.md
│   ├── logo.svg
│   └── logo-mark.svg
├── 04-ux-package/
│   ├── journey.md
│   ├── wireframes.md
│   └── mockups/
│       ├── 00-index.html
│       ├── 01-dashboard.html
│       ├── 02-scope.html
│       ├── 03-live-timeline.html
│       ├── 04-findings.html
│       ├── 05-chain-detail.html
│       ├── 06-report.html
│       ├── 07-settings.html
│       ├── screens.md
│       └── assets/styles.css
└── final/
    ├── phase1-report.md            (this file)
    └── github-copilot-build-spec.md
```
