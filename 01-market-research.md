# 01 — Market Research Consolidation

**Project:** Agentic Vulnerability Scanner (AVS)
**Author:** PM (one-man-company orchestrator)
**Date:** 2026-04-30 (Asia/Bangkok)
**Source:** distilled from `research-competitive.md` — refer there for full citations.
**Out of scope** (per user clarification 2026-04-30): pricing, costing, marketing, GTM, revenue projections.

---

## 1. The Two Halves of the Market

| Cohort | Sells | Examples | Core Limitation |
|---|---|---|---|
| **Legacy VM scanners** | CVE coverage + compliance reports | Tenable Nessus, Qualys VMDR, Rapid7 InsightVM, OpenVAS/Greenbone, Microsoft Defender VM | Per-vuln view; no chain reasoning; English-only output |
| **Autonomous / agentic pentest** | Exploit validation + attack-path narratives | Pentera, Horizon3.ai NodeZero, XBOW, Mindgard, RunSybil | Vendor-self-reported claims; narrow surfaces; not localized |
| **OSS execution layer** | Free commodity primitives | Nmap, Nuclei, Trivy, Burp, ZAP, Metasploit, Caldera, Prowler, ScoutSuite, Pacu, BloodHound, Syft/Grype | Coordination + reporting layer is the buyer's problem |

The strategic implication is unambiguous: **the moat is in orchestration, exploit-chain reasoning, evidence handling, and Thai/English reporting** — *not* in re-implementing recon or vulnerability detection.

## 2. State of LLM-Driven Security Agents (2024–2026)

Real, citable evidence that LLM agents do non-trivial offensive work in narrow contexts:

- **Google Big Sleep** found CVE-2025-6965 in SQLite (July 2025) — the first publicly attributed AI-discovered, near-in-the-wild zero-day.
- **UIUC paper (arXiv 2404.08144)** — GPT-4 with CVE-in-context exploited 87% of a 15-vuln test set; without the CVE description, success collapsed to ~7%. **This is the most important nuance in the literature** — agents work *much better* when grounded in CVE/EPSS data than when asked to discover novel bugs cold.
- **XBOW** reached #1 US HackerOne (~June 2025), $75M Series B (Altimeter / Sequoia).
- **Meta CyberSecEval 2/3** quantifies prompt-injection success at 26–41% across attack classes — robustness is measurable but imperfect.
- **Daniel Stenberg "AI slop"** — the canonical caution: agentic scanners that flood maintainers with plausible-sounding false positives are net-negative. **False-positive discipline must be a first-class product metric.**

## 3. Thailand Regulatory Pull (the structural opportunity)

Overlapping requirements on regulated Thai enterprises that incumbents do not localize:

| Driver | Effect on scan cadence / evidence |
|---|---|
| **PDPA** (eff. 1 Jun 2022; up to THB 5M per violation) | Scan logs may contain personal data → chain-of-custody, redaction, PDPC-aligned breach evidence required |
| **BoT IT Risk Management Guideline** (refresh late 2023) | Risk-based VA + pentest at least annually on critical systems; 30-day material-incident self-report |
| **Cybersecurity Act 2019 + CII regulations** (eff. 20 Jun 2024, NCSA) | CII operators must report cyber incidents on prescribed timelines; covers banking, telco, energy, transport, health |
| **PCI DSS 4.0** (full effect Mar 2024) | Quarterly external ASV scans + internal scans + post-change scans |
| **ISO 27001:2022 A.8.8** | Documented vulnerability management |

Thai-headquartered MSSPs (G-Able, MFEC, INET, ACIS, IRCT) currently resell global VM products; **no public data was found** on Thai market share by brand or service-mix revenue (flagged intelligence gap).

## 4. Buyer Pain Points (consistently reported)

1. **False-positive overload** (Pentera State of Pentesting 2025: avg enterprise = 75 tools, ~3,074 alerts/week at 101+-tool tier; 67% breached anyway).
2. **No exploitability prioritization** (CVSS-only doesn't tell you which 50 of 5,000 findings actually let an attacker reach the crown-jewel server).
3. **Weak remediation guidance** — findings rarely turn into ticketed, owner-assigned, time-boxed fixes.
4. **Multi-cloud + modern-asset blind spots** (Kubernetes, serverless, IaC, SaaS, Entra/AD/Okta identity, AI/LLM apps).
5. **Localization gaps for Thailand** — reports are English; PDPA evidence templates absent.
6. **Compliance-vs-attacker-reality mismatch** — clean compliance reports ≠ defensible against a real attacker.

## 5. Concept Scoring — Where AVS Should Wedge In

Scoring rubric (1–5; higher = better):

| Wedge | Differentiation | Defensibility | Time-to-Value | Fit to Thailand | **Total** |
|---|---|---|---|---|---|
| **A. Exploitability-first reporting (Thai + English)** | 5 | 4 | 4 | 5 | **18** |
| **B. PDPA-native evidence handling + chain-of-custody** | 5 | 5 | 3 | 5 | **18** |
| **C. Agentic FP-suppression as first-class metric** | 4 | 4 | 4 | 4 | **16** |
| **D. AI/LLM application coverage out of the box (MITRE ATLAS)** | 5 | 3 | 3 | 3 | **14** |
| **E. Cloud + IaC + identity in one chain** | 4 | 3 | 3 | 4 | **14** |
| **F. Continuous-validation cadence for BoT/PCI** | 3 | 3 | 4 | 5 | **15** |
| G. Generic "yet another VM scanner" | 1 | 1 | 4 | 1 | 7 |

**PM decision (tiebreaker):** wedges **A + B + C + F** form the MVP thesis. D and E are roadmap items for v1.x; G is rejected. The product is positioned as an **"Exploitability-first agentic scanner with Thai + English reporting and PDPA-native evidence."**

## 6. Competitive Positioning Statement

> For Thai enterprise security teams and MSSPs who are drowning in CVE lists and false positives, the Agentic Vulnerability Scanner (AVS) is an autonomous LLM-driven scanner that produces *exploitability-first* findings with chain-of-custody evidence, in Thai and English, mapped to PDPA / BoT / PCI / NCSA-CII obligations. Unlike Nessus / Qualys / Rapid7 (CVE coverage, English-only), and unlike Pentera / Horizon3 / XBOW (English-only attack-path validation), AVS combines exploit-chain reasoning with native Thai-language reporting, FP-suppression as a measured product metric, and an authorization-gate that is a *product feature* — not a checkbox.

## 7. Risks and Open Questions

- **Frontier-model providers may ship native security-agent SDKs** — orchestration moat erodes; mitigation = invest in evidence ledger + Thai localization + RoE-as-product.
- **Incumbent acquires an agentic-pentest player** (Tenable acquires Pentera, Microsoft acquires Horizon3) — compresses the differentiation window.
- **"AI slop" reputational damage** to the entire category — mitigation = aggressive FP discipline, evidence-only-by-default destructive checks.
- **Regulatory shift in PDPC enforcement** — out of our control; track quarterly.
- **No public benchmark** comparing Pentera / Horizon3 / XBOW on identical scope — we cannot calibrate exploit-coverage claims against them.

## 8. PM Conclusion

The market split is real, the LLM-agent capability evidence is real, and the Thai regulatory stack creates a structural pull no global incumbent localizes for. **The AVS thesis is supported.** Proceed to PRD with wedges A + B + C + F as the MVP.
