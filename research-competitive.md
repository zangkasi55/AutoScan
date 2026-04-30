# Agentic Vulnerability Scanner — Competitive Landscape & Capability Survey

**Project:** omc-agentic-vuln-scanner (Phase 1 research)
**Author:** OMC research thread (Claude Opus orchestrator)
**Date:** 2026-04-30 (Asia/Bangkok)
**Scope:** Defensive / authorized-pentest framing only. Pricing, COGS, and revenue projections are explicitly OUT OF SCOPE per `00-brief.md`.

---

## Executive Summary

The vulnerability-management market has bifurcated. On one side sit the legacy CVE-coverage scanners — Tenable Nessus, Qualys VMDR, Rapid7 InsightVM, OpenVAS / Greenbone, Microsoft Defender Vulnerability Management — which compete on plugin breadth, asset coverage, compliance reporting, and increasingly on "risk-based" prioritization layers [1][2][3][4][5]. On the other side, a new cohort of autonomous and agentic platforms — Pentera, Horizon3.ai NodeZero, XBOW, Mindgard, RunSybil — frames itself not as "scan and list" but as "validate and exploit", running attack chains against authorized environments to produce exploitability evidence rather than CVE inventories [6][7][8][9][10][11].

Around both sides, an open-source toolchain (Nmap, Masscan, Nuclei, Burp, ZAP, Metasploit, Caldera, Trivy/Grype/Syft, Prowler, ScoutSuite, Pacu) provides commodity primitives that any agentic system can wrap [18][19][20][21][22][23][24][25][26][27]. The state of the art in LLM-driven security agents — Google "Big Sleep" finding CVE-2025-6965 in SQLite, Meta CyberSecEval benchmarks, the UIUC "GPT-4 exploits one-day vulns at 87%" paper, and HackerOne's policy fights over "AI slop" — shows that agents can already do non-trivial discovery work, but with sharp caveats on novelty and false-positive risk [12][13][14][15][16][17].

For Thailand, regulatory drivers (PDPA, BoT IT Risk Guideline, Cybersecurity Act CII obligations, PCI DSS 4.0) push enterprises toward more frequent and better-evidenced scans, and create a defensible niche for a Thai-language, PDPA-aware, exploit-validating agentic scanner that incumbent global vendors do not localize well [28][29][30][31]. Buyer pain points — false-positive overload, no exploitability prioritization, weak remediation guidance, multi-cloud blind spots, and Thai-language gaps — are consistent across published surveys and practitioner commentary [32]. The differentiation opportunities for an agentic vulnerability scanner are concrete and listed in section 6.

**Confidence:** MODERATE-to-HIGH on incumbent positioning and regulatory drivers (multiple primary sources). MODERATE on agentic-platform claims (vendor self-reporting; corroborated where possible). LOW on Thai market sizing (no public data found).

---

## 1. Incumbent Vulnerability Scanners

The "VM" category — vulnerability management — is dominated by a small handful of vendors selling plugin-driven scanners with growing risk-scoring and asset-context layers.

**Tenable Nessus / Tenable.io / Tenable.sc (formerly SecurityCenter).** Nessus remains the volume leader by deployment, used by tens of thousands of organizations and underpinning Tenable.io (cloud) and Tenable.sc (on-prem console). The product's strength is plugin breadth — Tenable's research team ships templates for new CVEs typically within hours-to-days of disclosure, with documented coverage spanning OS, network device, database, web app, and container surfaces [1]. Tenable's roadmap has shifted toward "Exposure Management" — combining VM, ASM (attack surface management), and identity exposure (Tenable Identity Exposure, ex-Alsid) — but the underlying scanner is still a credentialed/uncredentialed plugin engine [1].

**Qualys VMDR.** Cloud-native architecture (agentless plus Cloud Agent), with VMDR (Vulnerability Management, Detection and Response) bundling discovery, prioritization (TruRisk score), patch orchestration, and EDR-adjacent functions. TotalCloud and CSAM (CyberSecurity Asset Management) extend coverage into cloud configuration and external attack surface [2]. Qualys's bet is integration: scanning, patching, EASM, and compliance evidence in one platform.

**Rapid7 InsightVM (formerly Nexpose).** Live dashboards, "Real Risk Score" combining CVSS with exploit availability, malware-kit presence, and vulnerability age, fed by both an Insight Agent and traditional scan engines [3]. Rapid7 differentiates on remediation projects, Goal/SLA tracking, and integration with InsightIDR (SIEM/XDR) and Metasploit (which Rapid7 owns) [3][22].

**OpenVAS / Greenbone Vulnerability Manager (GVM).** The dominant open-source scanner, GPL-licensed, maintained commercially by Greenbone. The Greenbone Community Feed publishes Network Vulnerability Tests (NVTs) covering tens of thousands of checks; the Enterprise Feed adds compliance content and faster updates [4]. OpenVAS is the de-facto fallback for cost-sensitive buyers and for embedding scan capability in larger products.

**Microsoft Defender Vulnerability Management.** Bundled with Microsoft Defender for Endpoint (and available as a standalone add-on), Defender VM uses the EDR sensor for continuous, agent-based VM and ties findings to Microsoft's secure-score and exposure model. Defender for Cloud extends coverage to Azure / AWS / GCP CSPM and container scanning [5]. Microsoft's structural advantage is presence — every Windows/Microsoft-365 estate already has the agent — and tight identity / patching integration via Intune.

**Common limitations of incumbents.** Scanner output is dominated by CVE-by-asset lists. Prioritization layers (TruRisk, Real Risk Score, Tenable's VPR) are improvements over raw CVSS but still operate on per-vuln scores, not chained-exploit reasoning. Compliance-mode scans optimize for clean reports, not for "what would actually let an attacker into the crown-jewel server" [1][2][3]. This is precisely the gap that the autonomous-pentest cohort exploits.

## 2. Autonomous / Agentic Pentest Platforms

A second cohort sells "automated security validation" or "autonomous pentest", framing the question not as "what CVEs do you have?" but "what attack paths actually work in your environment right now?".

**Pentera.** Israeli-origin, public-facing as the category creator of Automated Security Validation (ASV). The Pentera platform runs safe attack agents — credential discovery, lateral movement, privilege escalation, ransomware-emulation modules — across the live network and reports the realized attack paths. The April 22 2025 launch of "Pentera 7" added Distributed Attack Orchestration (multi-segment, geo-distributed validation) and AI-driven reporting that summarizes attack chains in narrative form [6]. Pentera's positioning sits inside the broader CTEM (Continuous Threat Exposure Management) frame popularized by Gartner.

**Horizon3.ai NodeZero.** US-headquartered, NodeZero markets itself as an autonomous pentest cloud service: customers deploy a lightweight orchestrator inside the perimeter; NodeZero discovers assets, attempts compromise chains (e.g., AD weaknesses, credential reuse, exposed services), and reports each finding with proof-of-exploitation and "Fix Actions" prioritized by realized impact [7]. NodeZero's AD Password Audit module is widely cited for surfacing actually-cracked Active Directory passwords rather than abstract policy violations [7].

**XBOW.** XBOW is the most aggressive entrant on the AI side. The company reached the #1 position on the US HackerOne leaderboard in approximately June 2025, with publicly reported submission counts above 1,000 and around 132 confirmed/triaged findings against participating bug-bounty programs, and raised a $75M Series B led by Altimeter (with Sequoia continuing) [8][9]. Co-founder Brendan Dolan-Gavitt comes from NYU offensive-security research [9]. XBOW's surface is principally web/application bug-bounty work, where the agent autonomously enumerates, fuzzes, and submits with PoC.

**Mindgard.** Lancaster University spinout focused on "DAST for AI" — dynamic application security testing of LLM-powered applications, mapped to MITRE ATLAS adversarial-ML tactics. The product probes deployed AI systems for prompt injection, jailbreak, model leakage, and supply-chain weaknesses; total disclosed funding around the $11.6M mark across rounds (2023-2024 timeframe) [10]. Mindgard's relevance to AVS is twofold: it points at a future-state surface (AI/LLM apps) that classical scanners do not cover, and it validates that DAST-style offensive testing is a viable wedge.

**RunSybil.** Khosla-Ventures-led $40M Series A announced March 18 2026, positioned as AI-native offensive security with the goal of replacing manual pentest engagements [11]. As of this writing, RunSybil's public technical disclosure is thinner than XBOW's; coverage emphasizes "agentic offensive" rather than a specific surface.

**Other 2024-2026 agentic players.** Public mentions and demoes (HackerOne hai, Bugcrowd's AI features, smaller startups using LangChain/AutoGen wrappers around Nuclei and Metasploit) have multiplied [16][33][34]. Most are immature; the category is consolidating around Pentera (validation), Horizon3 (network-internal pentest), XBOW (bug-bounty / web), and emerging AI-DAST players.

**Common limitations of agentic platforms.** Pentera and Horizon3 require deployed appliances/agents and explicit scope, and their public claims are vendor-supplied — there is **no public head-to-head benchmark** comparing them on identical scope (no public data found). XBOW's bug-bounty wins are real but operate in a "known-vuln-class on real-internet-targets" regime where public corpora exist. None of these platforms are known to be deeply localized for Thai-language reporting or PDPA evidence handling.

## 3. Open-Source Building Blocks

An agentic scanner does not need to reinvent recon, fingerprinting, or exploitation primitives. The open-source ecosystem already provides battle-tested, high-coverage tools.

**Network and host recon.** Nmap remains the canonical port/service/OS scanner with NSE (Nmap Scripting Engine) for thousands of probes [19]. Masscan and ZMap target high-volume Internet-scale enumeration. **ProjectDiscovery's stack** — Subfinder (subdomain enumeration), httpx (HTTP probing), and especially **Nuclei** (YAML-templated detection engine with 11,344+ community templates as of late 2024) — has become the de-facto agentic-friendly recon layer, because each tool is CLI-clean, JSON-output, and composable [18].

**Web and API testing.** Burp Suite (PortSwigger) is the industry-standard interactive proxy, with Burp Scanner for automated DAST and the Extender API for plugin work [20]. OWASP ZAP is the open-source counterpart, OWASP-backed, with automated and manual modes [21]. **sqlmap** for SQL injection, **ffuf** for content/parameter fuzzing, and **Nikto** for legacy web checks round out the OSS stack.

**Exploitation frameworks.** Metasploit (Rapid7-stewarded) provides modular exploit + payload + post-exploitation, and is the canonical reference for "is this CVE actually exploitable here?" [22]. **MITRE Caldera v5** provides asynchronous C2, the Magma Vue.js UI, and the Sandcat agent, with adversary-emulation flows mapped directly to MITRE ATT&CK techniques — a strong fit for chained-attack agents [23].

**Container, IaC, and SBOM.** Aqua Trivy, Anchore Grype, and Anchore Syft cover container image, OS package, and SBOM (CycloneDX/SPDX) scanning under permissive licenses; Trivy in particular has become the default container scanner in many CI pipelines [24].

**Cloud configuration auditing.** Prowler (300+ AWS-focused checks aligned to CIS, NIST, ISO; growing Azure/GCP support) [25]; ScoutSuite (NCC Group) for multi-cloud config audit across AWS/Azure/GCP/Aliyun/OCI [26]; and Pacu (Rhino Security Labs) for AWS-specific post-exploitation and privilege-escalation modules [27].

The strategic implication is that **the moat for an agentic scanner is not in re-implementing these primitives, but in the orchestration, exploit-chain reasoning, false-positive suppression, evidence-handling, and localization layers above them** [18][19][20][21][22][23][24][25][26][27].

## 4. State of LLM-Driven Security Agents

Public technical evidence on what LLM agents can and cannot do offensively has matured rapidly between 2024 and early 2026.

**Google "Big Sleep" / Project Naptime.** Google Project Zero introduced the "Naptime" framework in June 2024 as an LLM agent for vulnerability research, then partnered with Google DeepMind into "Big Sleep". In July 2025, Google publicly reported that Big Sleep had discovered **CVE-2025-6965** in SQLite — described as the first publicly attributed AI-discovered vulnerability that was on the verge of in-the-wild exploitation, found by an AI agent before threat actors weaponized it [12][13]. This is the strongest single proof point that LLM agents can do real-world novel-vulnerability discovery, when given the right tool harness and sandbox.

**Meta Purple Llama / CyberSecEval.** Meta's CyberSecEval 2 / 3 benchmark suite measures both *capability* (can the model write working exploits, MITRE ATT&CK helpfulness, autonomous-cyber tasks) and *safety* (prompt-injection resistance). Results across frontier models show prompt-injection success rates in the 26-41% range depending on attack class, and demonstrate that offensive-cyber uplift is **measurable but small** for fully novel tasks, larger for "complete this known exploit" tasks [14]. The benchmark is the most rigorous public yardstick for LLM cyber capability.

**UIUC one-day exploitation paper (Fang, Bindu, Gupta, Kang).** arXiv 2404.08144 reports that GPT-4 with a CVE description in context successfully exploited 87% of a 15-vulnerability test set; without the CVE description (closer-to-novel-discovery setting) success collapsed to ~7% [15]. This is the single most-cited result in the LLM-offsec literature, and the reason agentic scanners that can ingest CVE/EPSS data and target known vulnerable surfaces work *significantly better* than agents asked to discover novel bugs cold.

**HackerOne and Bugcrowd policies.** HackerOne shipped its "Hai" assistant and AI co-pilot for triage in 2024-2025, and updated its policy to permit AI-assisted submissions while explicitly banning bulk unverified low-quality reports [16]. Bugcrowd has taken similar policy positions. The platforms are pro-AI for triage and report-drafting, anti-AI for "spray and pray".

**Practitioner pushback — "AI slop".** Curl maintainer Daniel Stenberg has been the most visible voice flagging the cost of AI-generated false-positive bug reports — coined "AI slop" — describing the maintainer-side burden of triaging plausible-sounding but bogus AI-authored reports [17]. The Stenberg posts are now widely cited as the canonical caution that **agentic scanners must invest heavily in evidence and false-positive control or risk becoming negative-value generators** for downstream maintainers and security teams.

**Agentic frameworks.** The orchestration substrate has matured. **LangGraph** (LangChain) provides explicit state-graph control with persistence and human-in-the-loop checkpoints [33]. **CrewAI** offers role-based "crew" abstractions where each agent has a job and goal [34]. **Microsoft AutoGen / AG2** is conversation-driven multi-agent. **OpenAI Agents SDK** and Anthropic's tool-use / computer-use APIs provide vendor-native primitives. For an AVS-style system, LangGraph's explicit-state model is the closest fit for the "scan -> reason -> exploit -> verify -> report" chain that demands auditability.

**Net assessment.** LLM agents in 2026 can: (a) discover real novel vulnerabilities in narrow, well-instrumented contexts (Big Sleep), (b) reliably re-exploit known CVEs given description and tool access (UIUC), (c) draft acceptable-quality reports and reproduction steps (HackerOne hai, XBOW), and (d) operate with measurable but imperfect prompt-injection robustness (CyberSecEval). They cannot reliably do open-ended autonomous offensive work without scoping, tool harnesses, and human review. This shapes what AVS should and should not promise.

## 5. Thailand / Southeast Asia Context

Thailand's regulatory and ecosystem environment creates specific pressure points that a localized agentic scanner can serve.

**PDPA (Personal Data Protection Act).** Effective June 1 2022, modeled on GDPR. Maximum administrative penalties up to **THB 5 million** per violation, plus criminal and civil liability. The Personal Data Protection Committee (PDPC) is the enforcing authority and has issued sub-notifications on data-breach reporting and security measures [28]. For AVS, PDPA imposes hard requirements: scan logs may contain personal data and must be handled lawfully; chain-of-custody and access-control on evidence are non-negotiable.

**Bank of Thailand (BoT) IT Risk Management Guideline.** The BoT's IT-risk and cyber-resilience guidance was substantively refreshed in late 2023, requiring financial institutions to perform risk-based vulnerability assessments and penetration testing on critical systems at least annually, and to self-report material cyber incidents within 30 days [29]. Practical effect: every Thai bank already buys annual pentest, but the regulatory ceiling is rising toward continuous validation — directly in line with what agentic platforms sell.

**Cybersecurity Act and CII regime.** Under the 2019 Cybersecurity Act, the National Cyber Security Agency (NCSA) and National Cyber Security Committee designate Critical Information Infrastructure (CII) sectors. Sub-regulations on CII cyber-incident notification (announced 22 February 2024) took effect on **20 June 2024**, formalizing reporting timelines and scope for CII operators [30]. Sectors covered include national security, public services, banking and finance, IT and telecoms, transportation and logistics, energy and public utilities, and public health.

**PCI DSS 4.0.** Fully effective from March 2024, PCI DSS 4.0 retains and tightens the requirement for **external ASV scans quarterly and after every significant change**, plus internal vulnerability scans on the same cadence [31]. Any Thai merchant or acquirer in the cardholder-data scope faces this requirement directly.

**Thai MSSP landscape.** The principal Thai-headquartered MSSPs and security integrators include G-Able, MFEC, Internet Thailand (INET), ACIS Professional Center, and IRCT (and others). They typically resell global VM products (Nessus, Qualys, Rapid7) plus deliver pentest and SOC services [35]. **No public data was found** on the precise Thai market share of any specific scanner brand or on Thai MSSP scanning-service revenue mix; this is a known intelligence gap.

**ISO 27001 / 27002.** Annex A controls (e.g., A.8.8 "Management of technical vulnerabilities" in ISO 27001:2022) require documented vulnerability management and timely patching, which most Thai certified organizations operationalize via quarterly or monthly scans plus annual pentest.

**Net assessment.** Thai enterprises in regulated sectors face overlapping requirements — PDPA evidence handling, BoT pentest cadence, PCI ASV quarterly, NCSA CII reporting — that push toward continuous, well-evidenced, audit-trail-clean vulnerability work. Global scanners satisfy the technical requirements but rarely localize reports, evidence handling, or remediation guidance to Thai language and Thai operational context.

## 6. Buyer Pain Points & Differentiation Opportunities

### 6.1 Pain points (consistently reported)

1. **False-positive overload.** Pentera's "State of Pentesting 2025" survey reports the average enterprise runs 75 security tools and receives ~3,074 alerts per week at the 101+ tool tier, with 67% reporting a breach in the past 24 months despite the tooling [32]. Practitioner accounts (Stenberg "AI slop"; HackerOne triage backlogs) reinforce that signal-to-noise is the dominant cost driver [16][17].
2. **No exploitability prioritization.** CVSS-only scanner output cannot tell a customer which 50 of 5,000 findings are reachable, exploitable, and chainable to crown-jewel impact in their specific environment. This is the entire premise of Pentera/Horizon3/XBOW [6][7][8].
3. **Weak remediation guidance.** Findings rarely translate cleanly to ticketed, owner-assigned, time-boxed fix actions; remediation projects (Rapid7) and "Fix Actions" (Horizon3) are improvements but still leave the buyer to bridge the gap to internal change-management [3][7].
4. **Multi-cloud and modern-asset blind spots.** Coverage of Kubernetes, serverless, IaC, SaaS misconfigs, identity (Entra/AD/Okta), and AI/LLM apps is uneven. Mindgard's existence is itself evidence of the AI-app gap [10].
5. **Cost and licensing friction.** (Out of scope per `00-brief.md` — not analyzed here.)
6. **Localization gaps for Thailand.** Reports are English; remediation language assumes US/EU enterprise IT; PDPA-specific evidence templates are absent from the major vendors [28][29].
7. **Compliance-vs-attacker-reality mismatch.** Compliance scans optimize for clean reports rather than realistic attacker reasoning. Buyers know this and are increasingly buying ASV/CTEM tooling to compensate [6][32].

### 6.2 Differentiation Opportunities for an Agentic Scanner

These are the concrete gaps an agentic scanner with the AVS thesis (Claude orchestrator + GPT specialist agents) can credibly target:

1. **Exploitability-first reporting in Thai and English.** Default to chained-attack-path narratives (how an attacker would actually pivot) plus per-finding business-impact reasoning, rendered natively in Thai for SOC/CISO audiences and English for technical owners. Incumbents do not localize reports well [1][2][3][28].
2. **PDPA-native evidence handling.** Built-in chain-of-custody, redaction of personal data captured incidentally during scanning, and PDPC-aligned breach-evidence templates. This is a regulatory feature global vendors have not invested in [28].
3. **Agentic false-positive triage.** Use LLM specialist agents to corroborate every "high"-severity finding with at least two independent signals (e.g., banner + behavior + auth response) before surfacing it to the customer, learning from the curl "AI slop" experience [17]. Treat FP suppression as a first-class product metric.
4. **Authorization gate as a product feature.** Refuse to scan without signed scope acknowledgement; embed rules-of-engagement (RoE) as a structured object the agent reads at every step; abort on scope-deviation. This is required by the project brief and is also an honest differentiator vs unbounded autonomous-pentest pitches [00-brief.md].
5. **AI / LLM application coverage out of the box.** Bundle MITRE-ATLAS-aligned probes (prompt injection, jailbreak, training-data leakage, model-supply-chain) so AVS covers AI apps as a first-class surface — a gap no major Thai-MSSP-resold incumbent fills [10][14].
6. **Cloud + IaC + identity in one chain.** Wrap Prowler + ScoutSuite + Pacu primitives behind an exploit-chain reasoner so the report shows "misconfigured S3 -> credential exposure -> assumed role -> lateral to RDS" rather than three disconnected findings [25][26][27].
7. **Open-source-first execution layer.** Treat Nuclei, Nmap, Trivy, ZAP, Burp (where licensed), Caldera as commodity executors; invest in the orchestration, exploit-chain reasoning, evidence ledger, and Thai/English narrative layers above them [18][19][21][23][24].
8. **Model-diversity safety net.** Use Claude Opus for long-context orchestration and final synthesis, GPT-5.5 family for parallel specialist tasks (recon, evidence triage, report writing). Multi-vendor diversity reduces single-model blind spots and is a credible answer to enterprise procurement worries about LLM single-points-of-failure.
9. **Continuous-validation cadence for BoT/PCI customers.** Deliver scheduled, cadence-locked scans that produce regulator-ready evidence packages timestamped and hashed for the BoT 30-day reporting clause and PCI quarterly ASV requirement [29][31].
10. **Evidence-only-by-default destructive checks.** Make "verified-exploit-without-impact" the default; gate destructive checks per-asset behind explicit opt-in. This is both a safety constraint and a procurement-friendly differentiator vs less-disciplined autonomous platforms.

---

## Conclusion

The competitive landscape splits cleanly: **legacy scanners** sell CVE coverage and compliance reports; **autonomous-pentest platforms** sell exploit-validation and attack-path narratives; **open-source primitives** are a free commodity floor; and **LLM agents** are now demonstrably capable of real offensive work in narrow contexts (Big Sleep CVE-2025-6965, UIUC 87% one-day exploitation, XBOW #1 HackerOne) while still struggling with novelty and false-positive discipline (CyberSecEval, Stenberg "AI slop") [12][15][8][14][17].

**Why these patterns hold (causal reasoning):** The legacy scanners win on plugin breadth because each new CVE is incremental work and their research teams have a multi-decade content moat — but that same content-driven model gives them a per-vuln view of the world that cannot reason about chains. The autonomous-pentest cohort sells exactly the chain-reasoning that scanners cannot produce, but their offerings are still narrow (Pentera = network/AD; Horizon3 = internal pentest; XBOW = web bug-bounty), and their public proof points are vendor-supplied because the category lacks a neutral benchmark. LLM agents are uplift-positive but only when scoped, harnessed, and grounded in CVE/EPSS data — the UIUC paper's collapse from 87% to 7% when CVE descriptions are removed is the single most important nuance in the literature [15]. Practitioner pushback against "AI slop" tells us that the next durable advantage is not "more agents" but **agents that produce fewer, higher-quality, better-evidenced findings**.

For Thailand specifically, PDPA, BoT, NCSA CII obligations, and PCI DSS 4.0 quarterly scanning create a structural pull toward continuous validation with defensible evidence and Thai-language reporting [28][29][30][31] — a pull that no global incumbent currently serves cleanly. The differentiation opportunities above (exploitability-first Thai/English reporting, PDPA-native evidence, FP-suppression as a metric, authorization-gate as a product feature, AI/LLM-app coverage, multi-cloud chain reasoning, multi-model orchestration, continuous-validation cadence, evidence-only destructive defaults) are concrete and individually defensible.

**Confidence calibration.** HIGH on incumbent positioning (multiple primary sources [1]-[5]). HIGH on Thai regulatory drivers (primary regulator publications [28]-[31]). MODERATE on agentic-platform claims (vendor-supplied; corroborated where possible [6]-[11]). HIGH on the LLM-agent state-of-the-art evidence base (peer-reviewed and primary sources [12]-[17]). LOW on Thai market sizing (no public data found — flagged).

**Residual risks (pre-mortem).** (a) The agentic-pentest category may consolidate faster than expected — a Pentera/Horizon3 acquisition by a Tenable/Qualys/Microsoft would compress the window. (b) Frontier-model providers may ship native "security agent" SDKs, eroding the orchestration moat. (c) PDPA enforcement intensity could change with PDPC priorities. (d) "AI slop" reputational damage to the category is real and demands disciplined FP control.

**Limitations of this report.** No public head-to-head benchmark exists for Pentera vs Horizon3 vs XBOW on identical scope. Thai-specific scanner-market revenue and MSSP service-mix data is not publicly available. Vendor self-reporting was used where independent corroboration was unavailable, and is flagged as such. Pricing, COGS, and revenue projections are explicitly excluded from this round per `00-brief.md`.

---

## References

[1] Tenable, "Nessus" product page and Tenable.io / Tenable.sc documentation. https://www.tenable.com/products/nessus
[2] Qualys, "Vulnerability Management, Detection and Response (VMDR)." https://www.qualys.com/apps/vulnerability-management-detection-response/
[3] Rapid7, "InsightVM" product page and Real Risk Score documentation. https://www.rapid7.com/products/insightvm/
[4] Greenbone, "Community Edition (OpenVAS / GVM)." https://www.greenbone.net/en/community-edition/
[5] Microsoft, "Microsoft Defender Vulnerability Management" documentation. https://learn.microsoft.com/en-us/defender-vulnerability-management/
[6] Pentera, "Automated Security Validation" and "Pentera 7" launch (22 April 2025), press materials. https://pentera.io/
[7] Horizon3.ai, "NodeZero Autonomous Pentest" platform documentation. https://horizon3.ai/
[8] XBOW, "XBOW scores top rank on HackerOne US leaderboard" announcement (June 2025). https://xbow.com/blog/xbow-scores-top-rank/
[9] TechCrunch, "AI-powered bug hunter XBOW raises $75 million" (24 June 2025). https://techcrunch.com/2025/06/24/ai-powered-bug-hunter-xbow-raises-75-million/
[10] Mindgard, company site and DAST-AI / MITRE ATLAS-aligned product overview (2024). https://mindgard.ai/
[11] RunSybil, Khosla Ventures-led $40M Series A announcement (18 March 2026). https://www.runsybil.com/
[12] Google Project Zero / DeepMind, "Big Sleep" vulnerability research and CVE-2025-6965 SQLite disclosure (July 2025). https://googleprojectzero.blogspot.com/2025/07/
[13] Google Project Zero, "Project Naptime: Evaluating Offensive Security Capabilities of Large Language Models" (June 2024). https://googleprojectzero.blogspot.com/2024/06/project-naptime.html
[14] Meta, "CyberSecEval 2 / 3" benchmark suite, Purple Llama. https://ai.meta.com/research/publications/cyberseceval-2/
[15] Fang, Bindu, Gupta, Kang, "LLM Agents can Autonomously Exploit One-day Vulnerabilities," arXiv:2404.08144 (2024). https://arxiv.org/abs/2404.08144
[16] HackerOne, AI-assisted disclosure policy and "Hai" assistant documentation. https://www.hackerone.com/ai
[17] Daniel Stenberg, "The I in LLM stands for intelligence" / "AI slop" follow-ups, daniel.haxx.se blog (Jan 2024 onward). https://daniel.haxx.se/blog/2024/01/02/the-i-in-llm-stands-for-intelligence/
[18] ProjectDiscovery, "Nuclei templates" GitHub repository (11,344+ templates). https://github.com/projectdiscovery/nuclei-templates
[19] Nmap project, official site and NSE documentation. https://nmap.org/
[20] PortSwigger, "Burp Suite" product and Extender API documentation. https://portswigger.net/burp
[21] OWASP, "Zed Attack Proxy (ZAP)" project. https://www.zaproxy.org/
[22] Rapid7 / Metasploit project, framework documentation. https://www.metasploit.com/
[23] MITRE, "Caldera v5" project documentation. https://caldera.mitre.org/
[24] Aqua Security / Anchore, "Trivy / Grype / Syft" documentation, CycloneDX/SPDX SBOM support. https://aquasecurity.github.io/trivy/
[25] Prowler, official documentation (300+ checks across CIS / NIST / ISO). https://docs.prowler.com/
[26] NCC Group, "ScoutSuite" multi-cloud auditing tool. https://github.com/nccgroup/ScoutSuite
[27] Rhino Security Labs, "Pacu" AWS exploitation framework. https://github.com/RhinoSecurityLabs/pacu
[28] Office of the Personal Data Protection Committee (PDPC), Thailand PDPA portal and sub-notifications. https://www.dataprotection.go.th/
[29] Bank of Thailand, IT Risk Management Guideline / cyber resilience policy hub (refresh, late 2023). https://www.bot.or.th/en/financial-innovation/digital-finance/cyber-resilience.html
[30] National Cyber Security Agency (NCSA) Thailand, Cybersecurity Act 2019 and Critical Information Infrastructure sub-regulations (announced 22 Feb 2024; effective 20 June 2024). https://www.ncsa.or.th/
[31] PCI Security Standards Council, "PCI DSS v4.0" Requirement 11.3 external/internal vulnerability scanning. https://www.pcisecuritystandards.org/document_library/
[32] Pentera, "State of Pentesting 2025" survey report (April 2025). https://pentera.io/state-of-pentesting/
[33] LangChain, "LangGraph" documentation (state-graph agent orchestration). https://langchain-ai.github.io/langgraph/
[34] CrewAI documentation and Microsoft AutoGen / AG2 documentation. https://www.crewai.com/ ; https://microsoft.github.io/autogen/
[35] Thai MSSP / SI public sites — G-Able, MFEC, Internet Thailand (INET), ACIS Professional Center, IRCT. https://g-able.com/ ; https://www.mfec.co.th/ ; https://www.inet.co.th/ ; https://www.acisonline.net/

---

*End of report. Saved to `/mnt/workspace/working/omc-agentic-vuln-scanner/research-competitive.md`.*
