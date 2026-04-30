# 07 — Test Report (Phase 1: design & mockup pass)

> Phase 1 has no production code. The tester role here verifies the **design package** — PRD, architecture, journey, wireframes, and HTML mockups — for completeness, internal consistency, safety/compliance coverage, and bilingual contract.

Run date: 2026-04-30  ·  Tester: omc-tester (consolidated)  ·  Phase: 1

---

## 1. Scope of this pass

| Artifact | Location | Reviewed |
|----------|----------|----------|
| Brief | `00-brief.md` | ✓ |
| Competitive research | `research-competitive.md` | ✓ |
| Technical research | `research-technical.md` | ✓ |
| Market research consolidation | `01-market-research.md` | ✓ |
| PRD | `02-prd.md` | ✓ |
| Brand / CI | `brand/ci-guide.md` + `logo.svg` + `logo-mark.svg` | ✓ |
| Architecture | `05-architecture.md` (8 ADRs) | ✓ |
| UX journey | `04-ux-package/journey.md` | ✓ |
| Wireframes | `04-ux-package/wireframes.md` | ✓ |
| Mockups | `04-ux-package/mockups/00–07.html` + `assets/styles.css` | ✓ |

Marketing / pricing / GTM artifacts are intentionally absent per user instruction "I don't want to price, costing, marketing." This is a documented exclusion, not a gap.

---

## 2. Test cases & results

### 2.1 PRD vs research

| ID | Check | Result |
|----|-------|--------|
| T-PRD-1 | Every PRD principle traces to a research-backed differentiator. | **Pass** — 7 principles all map to a concrete source (PentestGPT, Big Sleep, XBOW, Pentera, MITRE Caldera MCP, PDPA, NCSA-CII). |
| T-PRD-2 | Personas reflect Thai market context (banking, MSSP, internal red team). | **Pass** — Khun Pim/Aek/Wit are mapped to BoT-regulated bank, MSSP, and internal red team respectively. |
| T-PRD-3 | Out-of-scope items explicit. | **Pass** — v0.1 excludes SaaS-hosted offering, AI/LLM-app probes (deferred to v1.1), pricing/marketing. |
| T-PRD-4 | Success metrics include FP rate, gate violations, MTTR. | **Pass** — FP ≤5%, 0 authorization-gate violations, chain-validation latency < 8 min p95. |

### 2.2 Architecture vs PRD

| ID | Check | Result |
|----|-------|--------|
| T-ARCH-1 | Every PRD capability has a corresponding ADR or component. | **Pass** — RoE → ADR-1 (MCP) + ADR-3 (sandbox); evidence-only by default → ADR-6; multi-vendor LLM → ADR-2; bilingual → ADR-8. |
| T-ARCH-2 | Sandbox boundary clearly defined for destructive actions. | **Pass** — Firecracker microVM clones are referenced in mockup `05-chain-detail.html` step-2 evidence card and in ADR-3. |
| T-ARCH-3 | Evidence ledger is tamper-evident (Merkle + RFC 3161). | **Pass** — Documented in ADR-4 and visualized in mockups (`evd-` chips, ledger anchor in scope sign step, audit trail in chain detail). |
| T-ARCH-4 | Scoring stack is multi-signal (CVSS+EPSS+KEV+SSVC+reachability). | **Pass** — ADR-5 covers all five signals; mockup `04-findings.html` displays four of five chip types. |

### 2.3 Mockups · functional walk

| ID | Check | Result |
|----|-------|--------|
| T-UI-1 | Top-nav and sidebar are present on every authenticated screen and link consistently. | **Pass** — all 7 screens share the identical chrome from `styles.css`. |
| T-UI-2 | Bilingual contract: every customer-facing label appears in both EN and TH. | **Pass with note** — The `.bi` pattern is applied to every finding/chain title; KPI tiles include `label` + `label-th`. Report preview includes both EN+TH paragraphs. *Action: enforce via `i18n-lint` once production build starts.* |
| T-UI-3 | Severity colors match the design tokens (`--sev-critical` etc.). | **Pass** — chips and badges all inherit from CSS custom properties. |
| T-UI-4 | Authorization is shown as a runtime feature, not a checkbox. | **Pass** — `02-scope.html` shows JWS preview, WebAuthn step, ledger anchor; `03-live-timeline.html` shows policy-stop event for an out-of-scope target (203.144.128.42 denied via exclusion list). |
| T-UI-5 | Evidence chains are displayed end-to-end. | **Pass** — `05-chain-detail.html` step-by-step card chain with `evd-118 / evd-143 / evd-144 / evd-145` and ledger anchors. |
| T-UI-6 | Destructive actions are gated visually. | **Pass** — `02-scope.html` test-categories table shows DoS as `forbidden`; chain-validation defaults to `evidence-only` chip. |
| T-UI-7 | Model router exposes per-role primary + fallback. | **Pass** — `07-settings.html` lists 6 roles with two `<select>` dropdowns each (primary/fallback) and tools-allowed scope per role. |
| T-UI-8 | Token / latency telemetry visible to operator. | **Pass** — `07-settings.html` token-usage table includes input/output token counts and p95 latency per role; pricing intentionally omitted. |
| T-UI-9 | Compliance mapping is explicit. | **Pass** — `06-report.html` cover lists PDPA Art. 37, BoT IT Risk Guideline §5, PCI DSS 4.0 Req. 1.4 / 6.4.1 / 11.4, NCSA CII Banking sector. |
| T-UI-10 | Language toggle in footer. | **Pass** — every screen shows the EN/TH lang-toggle in the footer. |

### 2.4 Safety / compliance review

| ID | Check | Result |
|----|-------|--------|
| T-SAFE-1 | Authorization gate cannot be bypassed via UI. | **Pass** — scan cannot start without signed RoE; `03-live-timeline.html` header pins the JWS hash and shows ledger TX. |
| T-SAFE-2 | Out-of-scope assets are visibly rejected. | **Pass** — see T-UI-4. |
| T-SAFE-3 | PDPA auto-redaction is on by default. | **Pass** — `06-report.html` audit-policy panel shows `redaction on` chip and explanation. |
| T-SAFE-4 | DPO sign-off is in the regulator-export flow. | **Pass** — bundle requires DPO co-sign. |
| T-SAFE-5 | Evidence ledger is tamper-evident in the user-visible flow, not just the back-end. | **Pass** — bundle hash, ledger root, TSA all surface in the report preview footer. |
| T-SAFE-6 | OWASP LLM Top 10 controls are referenced. | **Pass** — `07-settings.html` security panel lists prompt-injection isolation, output validation, supply-chain pinning. |

### 2.5 Bilingual contract — sample audit

Sampled 20 user-facing strings across screens:

- Navigation labels: Thai equivalent present in sidebar (e.g., "🛡️ Scopes (RoE)" + "ขอบเขตและกฎการทดสอบ" subtitles on the Scopes page).
- KPI labels: 4 of 4 in `01-dashboard.html` have `label-th`.
- Finding cards: 5 of 5 sampled cards have `.bi > .en + .th` blocks.
- Test-category rows: 6 of 6 in `02-scope.html` have `.bi`.
- Compliance chips: bilingual (e.g., "On track" + "การสแกน ASV รายไตรมาส").

**Bilingual coverage in mockups: 100% on sampled strings.**

---

## 3. Issues found

### 3.1 Severity 1 (blockers) — none.

### 3.2 Severity 2 (should-fix before pitch)

| ID | Description | Recommendation |
|----|-------------|----------------|
| ISS-S2-1 | Mockup screens use a single demo tenant ("SCB Tech"). | Acceptable for Phase 1 pitch deck. Production should make it tenant-driven. |
| ISS-S2-2 | Sandbox replay shown as Firecracker; gVisor mentioned in research as alternative. | Documented as ADR-3 alternatives. No action; both are valid. |

### 3.3 Severity 3 (notes for Phase 2)

| ID | Description | Owner in Phase 2 |
|----|-------------|------------------|
| ISS-S3-1 | i18n-lint not yet implemented; bilingual contract is honored manually in mockups. | Developer (Phase 2). |
| ISS-S3-2 | Real Critic agent must be sandboxed with no shared context window — verify in Phase 2 implementation. | Architect → Developer. |
| ISS-S3-3 | Token/latency telemetry shown statically; Phase 2 must wire OpenTelemetry. | Developer. |
| ISS-S3-4 | Some mockup tables (e.g., test-categories) use `<select>` styled elements; full state machine for "destructive opt-in per asset" is described in PRD but not yet visualized. | UX → Developer (Phase 2 v0.2 iteration). |

---

## 4. Known-gaps consolidation

Forwarded to `known-gaps.md`:
- ADR-2 (multi-vendor) increases operational surface; need provider-failure runbook.
- Critic agent's effectiveness depends on independent context — must be enforced at runtime, not just by convention.
- Bilingual contract enforcement must move from manual to build-time (`i18n-lint`).
- AI/LLM-app probing deferred to v1.1; OWASP LLM Top 10 mappings are advisory in v0.1.

---

## 5. Verdict

**Phase 1 design package is internally consistent, traceable, and ready to drive Phase 2 implementation via the GitHub Copilot build spec.** No SEV-1 issues. SEV-2/3 issues are tracked and either accepted as Phase 1 scope decisions or routed to Phase 2.
