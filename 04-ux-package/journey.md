# 04 — User Journey

**Project:** AVS / Sentry-AI
**Audience:** primary persona Khun Pim (internal VM lead); secondary Khun Aek (MSSP) and Khun Wit (red team).

---

## Stage 0 — Trust establishment (pre-product)

Before Pim ever logs in, she has seen:
- The product brief in Thai, with PDPA/BoT/PCI/NCSA-CII alignment statements.
- A signed RoE template she can take to her CISO.
- A live-demo video showing the **Authorization Gate** refusing to scan an out-of-scope target.

**Outcome:** Pim believes "this product cannot accidentally scan something we did not authorize."

## Stage 1 — Onboarding & First Tenant

1. Admin (Pim) signs in via Entra ID (OIDC) + WebAuthn.
2. Tenant wizard:
   - Brand (logo upload, color override of `--avs-shield`/`--avs-pulse` if MSSP).
   - Language preference (default Thai; English available).
   - Data residency (th-central-1 / on-prem cluster id).
3. KMS bootstrap — system generates a per-tenant key, wraps with customer-controlled HSM key, displays a *recovery shard* the analyst must store.
4. Integrations: connect Jira / ServiceNow / Slack / Microsoft Teams (optional).

**Outcome:** Tenant exists, branded, residency confirmed, integrations wired.

## Stage 2 — Define Scope (Rules of Engagement)

1. Pim clicks **New Scope** → wizard or upload existing scope doc (PDF / Word / JSON).
2. AVS extracts a structured RoE preview:
   - In-scope CIDRs / domains / cloud accounts (validated, dedup, reverse-DNS preview).
   - Exclusion list.
   - Allowed test categories (recon ✓, vuln ✓, destructive ✗ by default).
   - Time window (e.g., "weekdays 18:00–06:00 ICT only").
   - Contact tree (incident escalation in Thai + English).
   - Per-asset opt-ins (pre-populated empty).
3. Pim reviews each line, can add notes.
4. **RoE Signer** receives an email; opens the signing page; reviews the diff vs. last RoE; signs (OIDC + WebAuthn step-up).
5. RoE persisted, JWS-signed, hash-anchored in Evidence Ledger.

**Outcome:** A signed, machine-enforceable RoE exists. The product cannot scan without one.

## Stage 3 — Plan & Start Scan

1. Pim opens **Scans → New** and selects the signed RoE.
2. AVS Planner (Claude Opus) shows a proposed plan in plain Thai+English:
   - "I will discover assets across <CIDRs>, run vulnerability checks on services, and produce a chain-aware report. I will *not* run destructive checks."
   - Estimated duration; expected MCP tool list; rate cap.
3. Pim hits **Start**. The Live Timeline opens.

## Stage 4 — Live Timeline (the trust surface)

The timeline is the screen Pim watches. It shows, second-by-second:

- **Agent activity stream** (Recon, Vuln, Exploit-Reason, Critic, Report-Writer) — each agent is a swim-lane.
- Each row: agent → MCP tool call → target → result summary → evidence hash.
- A **policy badge** on every row: ✓ in-scope / ⚠ paused / ✗ refused (with reason).
- Live counters: assets discovered, findings raw, findings promoted, chains detected.
- Buttons: **Pause**, **Resume**, **Abort** (5-second hard-stop).

**Outcome:** Pim has full audit visibility while the scan runs.

## Stage 5 — Findings & Chains

When the scan completes (or at any pause), Pim opens **Findings**:

- **Top Chains** view (default): the top 10 attack chains, ranked by reachability + impact. Each chain is a graph; click expands to the constituent findings.
- **All Findings** view: filterable by severity / surface / asset / EPSS / KEV / SSVC.
- **Diff vs last scan**: new ✚ / recurring ↻ / resolved ✓.

Per finding card:
- Headline score 0–100 + sub-scores (CVSS 4.0, EPSS, KEV, SSVC, chain).
- Bilingual title + summary.
- Reproduction steps (curl / nuclei / nmap commands).
- Evidence chips (`evd-c8f3…2a4b`) — click to view raw artifact (with access-trail logging).
- Remediation block — patch link, IaC fix, code snippet.
- Buttons: **Push to Jira**, **Export PDF**, **Mark FP**, **Snooze**.

## Stage 6 — Remediation

1. Pim selects 12 chains → **Push to Jira**.
2. AVS pre-fills tickets in Thai (description, owner team) + English (commit-message guidance, patch URL).
3. Tickets land in the right project per AVS↔Jira mapping; SLAs start.
4. As tickets close, AVS re-runs targeted verification scans on those assets.

## Stage 7 — Compliance / Regulator Pack

1. Pim opens **Reports → Regulator Pack**.
2. Selects: PDPA / BoT / PCI / NCSA-CII (multi-select).
3. AVS assembles the bundle: signed PDF, hash manifest, evidence artifacts, RoE signature, scan timeline excerpts.
4. Hash root anchored to public RFC 3161 timestamp; bundle ID logged.
5. Pim downloads; gives to the regulator unchanged.

## Stage 8 — Continuous Validation

1. Pim sets a schedule: "every Monday 02:00 ICT."
2. Scans run automatically against the active signed RoE.
3. Diff reports posted to the SOC channel in Thai.
4. RoE expires (default 90 days) → automatic email reminder to RoE Signer to re-sign.

---

## End-to-end happy-path summary

```
Sign in → Define scope → Sign RoE → Start scan → Watch live timeline →
Review chains → Push tickets → Verify fixes → Generate regulator pack →
Schedule next run.
```

## Dark-path / safety branches

- **RoE not signed →** start-scan button disabled; tooltip in Thai+English.
- **Out-of-scope target appears in plan →** agent pauses; analyst must confirm or abort.
- **Destructive check requested →** step-up MFA prompt; otherwise blocked.
- **Tool sandbox crash →** agent retries once, then fails the step; scan continues with degraded coverage; final report flags the gap.
- **PDPA-detected PII in payload →** auto-redacted in stored evidence; raw sealed; report indicates redaction count.
- **RoE expires mid-scan →** scan aborts cleanly; partial report emitted with "RoE expired" banner.
