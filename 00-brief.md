# Project Brief — Agentic Vulnerability Scanner (AVS)

**Created:** 2026-04-30T18:18+07:00 (Asia/Bangkok)
**Owner:** Jimmy Danai Theptanawatana (danait@microsoft.com)
**Project slug:** agentic-vuln-scanner

## One-line concept

A multi-model agentic security tool that autonomously scans infrastructure and networks
to discover vulnerabilities, orchestrated by Claude Opus 4.7 with specialized GPT-5.5
sub-agents.

## Models

- **Orchestrator / reasoning brain:** Claude Opus 4.7
- **Specialist agents (multi-model):** GPT-5.5 family — used for recon, exploitation
  analysis, evidence triage, and human-readable report writing.
- Rationale for split: use Claude Opus for long-context reasoning and orchestration;
  use GPT-5.5 family for parallel specialist tasks where multi-vendor diversity reduces
  single-model blind spots.

## Target users

- Thailand enterprise blue / red / purple teams (banks, telcos, energy, government).
- Managed Security Service Providers (MSSPs) selling continuous attack-surface coverage.
- Internal vulnerability management teams replacing or augmenting Nessus / Qualys.

## What the system must do (capability sketch)

1. Accept a scope definition (CIDR, domain list, cloud-account inventory) WITH a written
   authorization gate (rules of engagement) that the user must affirm before scan starts.
2. Autonomously discover assets across network, host, web, API, and cloud surfaces.
3. Identify vulnerabilities (CVE-mapped + misconfiguration + chained logic flaws).
4. Reason about exploitability and business impact (not just CVSS).
5. Produce a prioritized findings report with reproduction steps, evidence,
   and remediation guidance — in English and Thai.
6. PDPA-compliant logging and evidence handling.

## Phase 1 deliverables (what THIS run produces)

- Market research + competitive landscape (Nessus, Qualys, Rapid7 InsightVM, Tenable,
  Pentera, XBOW, Horizon3 NodeZero, plus emerging agentic players).
- Gap analysis vs incumbents.
- Concept scoring (which slice of the market to target first).
- PRD — feature list, user stories, success criteria, safety rails.
- Corporate Identity (logo, palette, typography).
- UX package (journey, wireframes, HTML/CSS sample screens).
- Reference architecture.
- HTML/CSS sample screens (Phase-1 mockups, no real scanner code yet).
- Test report on the mockups.
- Phase-1 consolidated report + pitch deck.
- **Extra deliverable:** GitHub Copilot build spec — a developer-ready document the
  user can hand to GitHub Copilot to build the real MVP later.

## EXCLUDED from this run (per user clarification 2026-04-30)

- Pricing, costing, COGS, unit economics
- Marketing plan, GTM content, channel strategy
- 10M THB Year-1 margin feasibility analysis
- Sales enablement collateral

The orchestrator's standard `omc-marketing` stage and any pricing/financial-model
work in the PRD are SKIPPED. The PM should not produce price points or revenue
projections.

## Hard safety / ethics constraints

- The tool MUST refuse to begin a scan without written authorization scope.
- The tool MUST NOT auto-exploit destructive payloads — exploitation reasoning is
  evidence-only by default, with destructive checks gated behind explicit per-asset opt-in.
- The tool MUST log every action for chain-of-custody (PDPA + audit).
- The tool MUST honor rate limits and exclusion lists.
- No use against third-party infrastructure without proof of authorization.

## Success criteria for Phase 1

- All artifacts above exist in `working/omc-agentic-vuln-scanner/` AND uploaded to
  OneDrive `OneManCompany/agentic-vuln-scanner/`.
- Every factual claim about the market / competitors is cited via `deep-research`
  or `web_search`.
- The GitHub Copilot build spec is detailed enough that a developer using Copilot
  can scaffold the MVP without further design work.
