# AVS Mockups · Screen Index

Open `00-index.html` in a browser to navigate.

| # | File | Purpose |
|---|------|---------|
| W0 | `00-index.html` | Hero landing page; gateway to all mockups. |
| W1 | `01-dashboard.html` | Posture overview · 4 KPI tiles · top 5 chains · compliance cadence · agent fleet. |
| W2 | `02-scope.html` | Rules-of-Engagement editor · scope/exclusions · WebAuthn signature · ledger anchor. |
| W3 | `03-live-timeline.html` | 6 swim-lanes (orchestrator + 5 specialists) · live counters · pause/abort. |
| W4 | `04-findings.html` | Filter rail · top-chains tab · bilingual finding cards · push-to-Jira. |
| W5 | `05-chain-detail.html` | Visual chain graph · bilingual narrative · per-step evidence · remediation · audit trail. |
| W6 | `06-report.html` | Audience picker · live preview · regulator-bundle assembly · signed export. |
| W7 | `07-settings.html` | Model router · token usage · security policies · audit & retention · integrations. |

## Design tokens

All screens share `assets/styles.css`. Color palette, typography, severity badges, and bilingual text styles come from the brand identity at `../../brand/ci-guide.md`.

## Bilingual contract

Every customer-facing string in the mockups appears in both English and Thai (using the `.bi > .en + .th` pattern). The Report-Writer agent in production must respect this contract via the `i18n-lint` build-time check.
