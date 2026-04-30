# 04 — Wireframes (low-fidelity reference)

> Polished HTML/CSS implementations of these wireframes live in `04-ux-package/mockups/*.html`. Open `index.html` in a browser to navigate them.

---

## Information architecture

```
Top nav:    [Logo]   Dashboard   Scopes   Scans   Findings   Reports   Settings   [Tenant]   [User]
Side panel: contextual filters
Footer:     [EN | TH] toggle · build hash · status
```

## W1 — Dashboard (`01-dashboard.html`)

Purpose: Pim's morning glance. "What changed?"

Sections:
1. **Posture summary** — 4 KPI tiles (Critical chains / Open criticals / KEV-listed open / FP rate).
2. **Latest scan timeline mini-strip** — last 24 h activity.
3. **Top 5 chains** — compressed cards.
4. **Compliance cadence** — chips for PCI quarterly, BoT annual, NCSA-CII reporting status.
5. **Agent fleet health** — orchestrator + 5 specialists + tool-server uptime.

## W2 — Scope / RoE (`02-scope.html`)

- Wizard or document-upload entry.
- Structured RoE editor: scope, exclusions, test categories, time window, contacts, per-asset destructive opt-ins.
- Signature panel — signer, OIDC subject, WebAuthn challenge, JWS preview.
- Hash + chain-anchor display once signed.

## W3 — Live Scan Timeline (`03-live-timeline.html`)

- Scan header: scope id, RoE hash, started-at, ETA, status pill.
- 5 swim-lanes (agents) on the left; each lane is an event list.
- Each event row: timestamp · MCP tool · target · summary · policy badge · evidence chip.
- Live counters strip: assets / raw findings / promoted / chains / FPs filtered.
- Action bar: Pause · Resume · Abort.

## W4 — Findings list (`04-findings.html`)

- Filter rail (severity, surface, asset tag, EPSS, KEV, SSVC, since-date).
- Top toolbar: Top-chains tab · All-findings tab · Diff tab.
- Cards: headline score, bilingual title, evidence chips, primary actions (Push Jira / Export / Mark FP).

## W5 — Chain Detail (`05-chain-detail.html`)

- Graph visualization (nodes = assets/findings; edges = exploitation relationship).
- Bilingual narrative ("How this chain works") in EN+TH.
- Per-step evidence drill-down.
- Business-impact estimator.
- Remediation block per node.

## W6 — Report / Regulator Pack (`06-report.html`)

- Audience picker: CISO / Analyst / Owner / Regulator.
- Live preview pane (HTML).
- Export controls: PDF (signed), CSV/Excel, STIX, CycloneDX.
- Regulator pack assembly: select PDPA / BoT / PCI / NCSA-CII; preview bundle manifest.

## W7 — Settings (`07-settings.html`)

- Tabs: Tenant · Brand · Integrations · Models · Security.
- Models tab shows the model-router config (per-role model + fallback).
- Security tab shows audit policies, retention, KMS, MFA enforcement.

## Navigation map (mockup index — `00-index.html`)

A landing index page links to all mockups for review.
