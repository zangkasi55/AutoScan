# Technical Reference — Agentic Vulnerability Scanner (AVS)

> **Scope.** Grounded technical reference for an autonomous, LLM-driven vulnerability scanner orchestrated by Claude Opus 4.7 with GPT-5.5 specialist sub-agents. Defensive / authorized testing only. All factual claims carry inline citations.
>
> **Confidence levels.** HIGH = corroborated by 2+ primary sources. MODERATE = single primary source or one primary plus secondary. LOW = inferred / forward-looking.
>
> **Build-spec note.** "Claude Opus 4.7" and "GPT-5.5" reflect the user's design intent at writing time (April 2026). The architectural reasoning generalises to current production model families; no public claim is made about specific model availability.

---

## Executive Summary

An Agentic Vulnerability Scanner (AVS) is best built as a **planner / executor / critic orchestration** pattern, where a high-context reasoning model (Claude Opus class) coordinates parallel specialist sub-agents (GPT-5.5 class) that wrap deterministic security tools through the **Model Context Protocol (MCP)** [1][2]. Prior art — PentestGPT [7], HackingBuddyGPT [8], Google's **Big Sleep** [10], and the Caldera **MCP plugin** [36] — establishes that LLM-driven offensive reasoning works in narrow domains today, with the strongest results when the LLM does not "do hacking" itself but rather *plans and interprets* output from battle-tested tools (Nmap, Nuclei, Trivy, Prowler, BloodHound, ZAP). Safety must be wired in at three layers: **OWASP LLM Top 10 (2025)** controls inside the agent loop [19][20], NIST AI RMF / AI 600-1 governance around the program [21][22], and hardware-isolated sandboxing (gVisor / Firecracker / Kata) at the tool execution boundary [26]. Findings should be scored using **CVSS 4.0 + EPSS + CISA KEV + SSVC** in combination, not CVSS alone [17][18][23][24]. **Confidence: HIGH** for architecture choices (well-corroborated), **MODERATE** for vendor-roadmap dependencies.

---

## 1. Multi-LLM Agent Orchestration Patterns

### 1.1 The planner / executor / critic loop

The dominant production pattern across Anthropic and OpenAI documentation is an **orchestrator-worker** (also called planner-executor) topology in which a central LLM decomposes a task, dispatches parallel sub-agents, and synthesizes their outputs. Anthropic's published research-system architecture explicitly uses one orchestrator (a Claude Opus-class model) that "decides on the approach and spawns subagents to explore different aspects simultaneously," each returning compressed findings to the lead [3]. OpenAI's Agents SDK formalizes the same pattern with primitives named **Sessions, Handoffs, Guardrails, and Tracing**, and supports **Sandbox Agents** for isolated tool execution [4][5]. For an AVS, this maps cleanly:

| Role | Model | Responsibilities |
|------|-------|------------------|
| **Planner** | Claude Opus 4.7 | Read scope/RoE; decompose into recon / vuln-scan / exploit-reasoning / report tasks; manage long-context evidence pool |
| **Recon executor** | GPT-5.5 specialist | Drive Nmap, Masscan, RustScan, ZAP spider; normalize asset graph |
| **Vuln executor** | GPT-5.5 specialist | Drive Nuclei, Trivy, Prowler, AWS Inspector; map findings to CVE/CWE |
| **Exploit-reasoning executor** | GPT-5.5 specialist | Reason about chainability and business impact (no destructive payloads) |
| **Critic / report writer** | GPT-5.5 specialist | Adversarial review, English+Thai narrative, evidence packaging |

**Why multi-vendor.** A single-model pipeline shares whatever blind spots that family has — including the same prompt-injection failure modes documented in **AgentDojo** (97 tasks / 629 prompt-injection test cases across multiple frontier models showed every model failing on a non-trivial subset) [11]. Routing critic and executor roles across vendors materially reduces correlated error. The same logic motivates Google's two-tier architecture: a research-grade **Sec-Gemini** feeds proven techniques into the production **SecLM** platform; both sit on Vertex AI rather than a single monolith [32][33]. **Confidence: HIGH.**

### 1.2 Tool use via Model Context Protocol (MCP)

The Model Context Protocol, originally announced by Anthropic and **donated to the Linux Foundation Agentic AI Foundation in December 2025**, is the de-facto standard for connecting agents to external tools and data [1][2]. MCP defines a **JSON-RPC 2.0** wire protocol with three roles: **hosts** (the agent app), **clients** (per-server connections inside the host), and **servers** (the tool wrappers) [1]. Practically, every scanner tool the AVS uses — Nmap, Nuclei, Trivy, BloodHound, etc. — should be wrapped as an **MCP server** exposing typed input schemas; the planner and executors consume them as MCP clients. MITRE has already shipped exactly this pattern: the **Caldera MCP plugin (Nov 2025)** wraps Caldera's REST API as an MCP server so an LLM can drive adversary-emulation operations end-to-end, with **MLflow** tracking every tool call and reasoning step [36][37]. This is direct precedent for an AVS architecture.

OpenAI's Responses API and Agents SDK also speak MCP natively, and Anthropic's tool-use API documents schema-driven definitions that are MCP-compatible by design [4][6]. For the AVS, MCP gives:

- **Vendor-agnostic tool layer** — replacing Claude with another model later does not break the tool wrappers.
- **Auditability** — every tool invocation is a typed JSON-RPC message, easy to log for PDPA/SOC2 chain-of-custody [35].
- **Composability** — the same MCP server (e.g., Trivy) is reused by the planner, the executor, and a human analyst's IDE.

### 1.3 Token-efficient long-running scans

Long scans (hours, hundreds of hosts) blow normal context windows. Four working patterns:

1. **Subagent compression** — subagents return only summaries to the planner, mirroring Anthropic's research system [3].
2. **External evidence pool** — PentestGPT's "Context Pool" persists findings to disk and re-injects the relevant slice per turn [7].
3. **Tool result truncation** — store full Nmap/Nuclei JSON externally, hand the LLM only N most-suspicious items.
4. **Checkpointing** — periodic state snapshots so a 12-hour scan can resume after a model rate-limit retry without re-running discovery.

**Confidence: HIGH** on patterns 1-3 (multiple sources); **MODERATE** on 4 (engineering common sense; not vendor-documented for security agents specifically).

---

## 2. Agentic Security Frameworks and Prior Art

| System | Year | Approach | Why it matters for AVS |
|--------|------|----------|------------------------|
| **PentestGPT** [7] | USENIX Sec '24 (Distinguished Artifact) | Three modules — *Reasoning*, *Tool*, *Parsing* — plus a persistent *Context Pool* | First peer-reviewed validation that LLM-driven pentesting works on HTB/VulnHub-class targets; reasoning/tool separation is the cleanest published blueprint |
| **HackingBuddyGPT** [8] | TU Wien / ipa-lab, ongoing | Agent / UseCase / Capability abstractions; OSS | Shows how to keep the agent loop minimal (~100 LOC core) and bolt domain capabilities on; good reference implementation |
| **Project Naptime → Big Sleep** [9][10] | Google Project Zero + DeepMind, 2024-2025 | Specialized tools: *Code Browser*, *Python*, *Debugger*, *Reporter* | First AI agent to find an in-the-wild SQLite zero-day actually being exploited (disclosed July 2025) — proof that agents can compete with senior researchers on real targets |
| **AgentDojo** [11] | ETH Zurich + Invariant Labs | 97 tasks, 629 prompt-injection security test cases | The canonical eval harness; AVS regression suite should include AgentDojo-style adversarial tool-use tests |
| **Caldera MCP plugin** [36][37] | MITRE, Nov 2025 | LLM-based ad-hoc planner + ability factory; RAG over STIX CTI | Direct architectural template — shows MCP wrapping a security framework's REST API works |
| **Microsoft Security Copilot** [12] | GA 2024+ | Skills + plugins + agentic execution; integrates Defender / Sentinel / Intune | Reference for enterprise integration surface and agent governance UX |

The clearest pattern across these systems: **the LLM never replaces the deterministic scanner — it plans, interprets, and chains scanner output**. PentestGPT explicitly delegates execution to the human/tool layer; Big Sleep's tools are well-tested deterministic primitives [7][9]. AVS should follow this rule. **Confidence: HIGH.**

---

## 3. Tool Integrations to Wrap

These are the deterministic building blocks the agents call. All should be MCP-wrapped with typed inputs (target, rate-limit, output-path) and structured outputs.

### 3.1 Network discovery

- **Nmap / Masscan / RustScan** — port and service discovery. Wrap with rate-limit and exclusion-list parameters bound to the RoE document.
- **OWASP ZAP — Automation Framework** — the modern way to drive ZAP is a **YAML automation plan** that combines `spider`, `spiderAjax`, `openapi`, `soap`, `graphql`, `passiveScan`, and `activeScan` jobs in one file [34]. The Automation Framework explicitly replaces the legacy CLI and packaged-scan modes [34]. Pair with Burp Suite Enterprise REST when commercial Burp is in scope.

### 3.2 Vulnerability and config scanning

- **Nuclei** — ProjectDiscovery's YAML-template scanner; the templates community is the largest active CVE-detection corpus [13].
- **Trivy** — Aqua's all-in-one scanner; produces SBOMs in **CycloneDX and SPDX** formats and scans containers, filesystems, IaC, and Kubernetes [14].
- **Grype + Syft** (Anchore) — pair Syft for SBOM generation with Grype for vulnerability matching; useful where Trivy's matchers disagree (cross-validation).
- **Prowler** — multi-cloud (AWS/Azure/GCP/Kubernetes) misconfiguration scanner with ~500+ checks; OSS, Apache 2.0 [15].
- **ScoutSuite** (NCC Group) — AWS/Azure/GCP audit; complements Prowler.

### 3.3 Cloud-native vulnerability services

- **AWS Amazon Inspector v2** — continuously scans EC2 (via SSM agent), ECR images, and Lambda functions; produces an **Inspector risk score** that combines CVSS base + network reachability adjustment + exploit-intelligence adjustment from CISA KEV [29][40]. Multi-account via delegated administrator.
- **Microsoft Defender for Cloud** — vulnerability-assessment + posture management, native integration into **Microsoft Sentinel** SIEM via the Defender XDR connector and Syslog/CEF/REST channels [30].
- **Google Cloud Security Command Center (SCC)** — Security Health Analytics + Web Security Scanner detectors; tiered Standard / Premium / Enterprise [31]. AVS should treat findings from SCC, Inspector, and Defender as *first-party signals* rather than re-scanning.

### 3.4 Identity / Active Directory

- **BloodHound CE** (SpecterOps) — graph-theoretic AD/Entra attack-path analysis; with v8 **OpenGraph**, extensible to GitHub, Okta, Jamf, etc. via JSON schema [27]. Collectors are **SharpHound** (AD) and **AzureHound** (Entra) [27].
- **PingCastle** — AD health-check tool; **free for non-profit and own-system audits**, paid commercial license for resale [28]. Binaries are digitally signed [28].

### 3.5 Credential testing — strict dual-use guardrails

**Hydra** and **Hashcat** are dual-use: legitimate password-policy testing on the customer's own assets vs. abusive cracking. AVS should:

- Disable by default; require explicit per-asset opt-in in the RoE.
- Cap brute-force depth (e.g., top-1000 list, 60-second wallclock).
- Log every attempt to the chain-of-custody store.
- Refuse to operate on hashes the system did not extract under the current RoE.

These constraints align with the AVS brief's "no destructive auto-exploit" rule and OWASP LLM Top 10's **LLM06 Excessive Agency** mitigation [19].

---

## 4. Vulnerability Data Sources

| Source | Use | Notes |
|--------|-----|-------|
| **NVD / CVE** | Authoritative CVE record; CPE; CVSS 3.1 + 4.0 vectors | NVD now publishes CVSS v4.0 alongside v3.1 [25] |
| **GitHub Advisory Database** | Ecosystem-aware (npm, PyPI, Maven, etc.) | Often faster than NVD for OSS |
| **OSV.dev** (OpenSSF) | Distributed vulnerability schema; **OSV-Scanner V2** with OSV-SCALIBR | Aggregates GHSA, RustSec, PyPA, Go vuln, etc. [16] |
| **CISA KEV catalog** (BOD 22-01) | Vendor-agnostic list of vulns with confirmed in-the-wild exploitation | Use as a "must-patch" override regardless of CVSS [17] |
| **EPSS** (FIRST) | Daily-updated probability (0-1) of exploitation in the next 30 days | Best single signal for *operational* prioritization [18] |
| **MITRE ATT&CK** | TTP taxonomy | Tag findings with ATT&CK techniques for blue-team consumption |
| **CWE** | Weakness taxonomy | Group root causes across many CVEs |

The AVS should **enrich every finding** with: NVD/OSV record + KEV flag + EPSS score + ATT&CK technique + CWE category. This is what Inspector v2 does internally [40] and what makes the difference between "data" and "decision-grade" findings. **Confidence: HIGH.**

---

## 5. Safety Rails for an Agentic Security Tool

### 5.1 OWASP LLM Top 10 (2025) — the agent-loop layer

The November 2024 release of OWASP's **Top 10 for LLM Applications, version 2025** is the canonical control set [19][20]. AVS-relevant items:

- **LLM01:2025 Prompt Injection** — primary risk when the agent ingests scanner output (e.g., a banner, an HTML page, a Nuclei template) that contains adversarial instructions. Mitigations: structured tool outputs, dedicated parser sub-agent, AgentDojo-style regression tests [11][19].
- **LLM02 Sensitive Information Disclosure** — scan evidence often contains credentials, PII, internal hostnames. Redact before LLM ingestion.
- **LLM06 Excessive Agency** — cap autonomous actions; require human-in-the-loop for any state-changing operation (the AVS brief already mandates this).
- **LLM05 Improper Output Handling** — sanitise any code-like content the agent emits before rendering or executing.
- **LLM10 Unbounded Consumption** — scan-cost runaway is a real risk; enforce token, time, and dollar caps per scan.

### 5.2 NIST AI RMF + AI 600-1 — the program layer

**NIST AI 100-1 (AI RMF)** organizes governance into four functions: **Govern, Map, Measure, Manage** [21]. **NIST AI 600-1**, the GenAI Profile, enumerates **12 GAI risks** including confabulation, prompt-injection, data privacy, information-security, and value-chain risks [22]. AVS should publish a one-page mapping from each AI 600-1 risk to its concrete control (e.g., confabulation → mandatory citation of source for every finding; data privacy → field-level redaction before LLM ingestion).

### 5.3 Authorization and Rules of Engagement

The brief mandates a written authorization gate. Reference patterns: **Cobalt** and **HackerOne** publish disclosure / engagement templates that AVS can mirror — scope, exclusions, hours, contacts, escalation, no-third-party clause. Encode the RoE as a *signed JSON document* the planner reads at scan start; refuse to start if absent or expired.

### 5.4 Sandbox isolation for tool execution

Tools run in a separate trust boundary from the agent loop. Three production-grade options:

| Option | Mechanism | Boot time | Best for |
|--------|-----------|-----------|----------|
| **gVisor** [26] | User-space kernel intercepts syscalls (Google) | <100 ms | Per-tool isolation with low overhead |
| **Firecracker** [26] | Lightweight VMM in Rust (AWS); KVM-backed microVMs; powers Lambda and Fargate | ~125 ms | Strong hardware-level isolation per scan |
| **Kata Containers** [26] | Orchestrates microVMs (Firecracker / Cloud Hypervisor / QEMU) under a Kubernetes/CRI interface | ~1-2 s | Drop-in for existing K8s clusters |

**Azure Container Apps** offers a managed equivalent with Hyper-V isolation. Recommendation: **Firecracker per-scan** (fresh microVM, ephemeral disk, network policy attached to RoE scope) for the strongest guarantee that one engagement cannot leak into another. **Confidence: HIGH.**

### 5.5 Kill-switch and chain-of-custody

- **Hard stop:** every executor sub-agent reads a "stop" flag (Redis key, MCP heartbeat); planner exits within one tool-call cycle.
- **Per-action audit log:** every MCP tool call → JSON line with timestamp, scope_id, actor (model id), inputs (hashed if sensitive), outputs (offloaded), human approver (if any).
- **PDPA Thailand (B.E. 2562 / 2019):** scan evidence frequently contains personal data of customer staff — names, emails, internal IDs [35]. Apply data-minimisation, purpose-limitation, and retention caps consistent with the act; appoint a DPO; honour data-subject access requests over scan archives.

---

## 6. Vendor Reference Architectures

| Vendor stack | Components | Lessons for AVS |
|--------------|------------|-----------------|
| **Microsoft Security Copilot + Defender for Cloud + Sentinel** [12][30] | Skills, plugins, promptbooks; ingest via Defender XDR connector or Syslog/CEF/REST | Treat AVS findings as a Sentinel data source; expose AVS as a Copilot **plugin** so analysts can ask natural-language follow-ups |
| **Google Cloud Security AI Workbench → SecLM / Sec-Gemini** [32][33] | Sec-PaLM (2023) → SecLM platform; Gemini in Google SecOps; Mandiant CTI grounding | Two-tier model split (research vs. production) is reusable; SCC findings as input [31] |
| **MITRE Caldera + MCP plugin** [36][37] | C2 server with REST API wrapped by MCP; LLM ability factory + planner; MLflow observability | Closest open-source template; AVS should adopt MLflow-style tracing |
| **Anthropic multi-agent research system** [3] | Orchestrator-worker with parallel subagents | Direct template for AVS planner |

The cross-cutting design principle: **agents on top, deterministic security platforms underneath**. Every vendor that has shipped is doing this. **Confidence: HIGH.**

---

## 7. Reporting and Scoring Standards

### 7.1 CVSS 3.1 vs 4.0

**CVSS v4.0** was released by FIRST on **November 1, 2023** and is officially supported by NVD as of June 2024 [24][25]. Key changes from v3.1:

- **Four metric groups**: Base, **Threat** (renamed from "Temporal"), Environmental, **Supplemental** (new) [24][38].
- New base metric **Attack Requirements (AT)** complements Attack Complexity by capturing prerequisite conditions of the vulnerable system [24][38][39].
- **User Interaction** split into Passive vs Active [39].
- **Impact split into Vulnerable System (VC/VI/VA) and Subsequent System (SC/SI/SA)** — replaces the awkward v3.1 Scope metric [39].
- New **Supplemental** metrics: Safety, Automatable, Recovery, Value Density, Provider Urgency, Vulnerability Response Effort — context only, do not change the score [24][38].
- New **nomenclature**: CVSS-B / CVSS-BE / CVSS-BT / CVSS-BTE depending on which groups are included [38].

**Recommendation:** AVS should **store both CVSS 3.1 and 4.0 vector strings** when available (NVD now publishes both [25]) and present whichever the customer's downstream tooling consumes. v3.1 is **not deprecated**; it remains widely used.

### 7.2 EPSS — operational prioritization

EPSS produces a **daily-updated probability between 0 and 1** that a CVE will be exploited in the next 30 days [18]. Use EPSS as the primary tie-breaker among CVEs of similar CVSS severity — a CVSS 7.5 with EPSS 0.95 is operationally more urgent than a CVSS 9.8 with EPSS 0.01.

### 7.3 SSVC — decision-tree prioritization

CISA's **Stakeholder-Specific Vulnerability Categorization (SSVC)** is a decision tree producing four actions: **Act / Attend / Track* / Track**, derived from Exploitation status, Technical Impact, Mission Impact, and Public Well-being Impact [23]. SSVC complements CVSS+EPSS by encoding **defender context** explicitly. AVS reports should output *both* a CVSS+EPSS score *and* an SSVC decision per finding.

### 7.4 KEV as a hard override

CISA KEV is the only signal that says "this is being exploited *right now*". Any finding mapped to a KEV entry should be marked **Act** in SSVC and surfaced at the top of the report regardless of CVSS [17].

### 7.5 DREAD — legacy only

Microsoft moved away from DREAD in modern SDL guidance because the subjective 1-10 scoring produces inconsistent results across analysts. Mention DREAD in the report only if a customer specifically requires it for legacy reasons; use CVSS 4.0 + EPSS + SSVC as the primary scoring stack.

### 7.6 Recommended report schema

```json
{
  "finding_id": "uuid",
  "cve_ids": ["CVE-2025-xxxxx"],
  "cwe": "CWE-79",
  "attck_techniques": ["T1190"],
  "cvss_v3_1": {"vector": "...", "base_score": 7.5},
  "cvss_v4_0": {"vector": "...", "base_score": 8.4, "supplemental": {...}},
  "epss": {"score": 0.92, "percentile": 0.99, "as_of": "2026-04-29"},
  "kev_listed": true,
  "ssvc_decision": "Act",
  "evidence": [{"tool": "nuclei", "template": "...", "request": "...", "response_hash": "..."}],
  "reasoning_trace_id": "mlflow-run-id",
  "remediation": {"en": "...", "th": "..."}
}
```

---

## Conclusion

**Why this architecture works.** The agentic-vulnerability-scanner space converges on one design because the constraints converge: (a) LLMs hallucinate too much to *be* the scanner, but reason well enough to *direct* one; (b) the security tool ecosystem (Nmap, Nuclei, Trivy, BloodHound, Inspector, SCC, Defender) is mature, deterministic, and already MCP-wrappable; (c) safety regimes (OWASP LLM Top 10, NIST AI RMF, PDPA, KEV) are sufficiently stable to design against. PentestGPT validated the planner/executor split academically [7]; Big Sleep validated it on a real zero-day [10]; Caldera's MCP plugin validated MCP as the integration substrate [36]. The remaining engineering risk is **operational**, not architectural: rate-limiting, evidence redaction, RoE enforcement, and chain-of-custody.

**Top three residual risks** (from pre-mortem):

1. **Prompt injection from scanner output** — banners and HTML can carry adversarial instructions. Mitigation: structured tool outputs, dedicated parser, AgentDojo regression suite [11][19].
2. **Vendor model drift** — capabilities of Claude / GPT change month-to-month. Mitigation: MCP isolation of the tool layer; the agent layer is replaceable.
3. **Misuse / dual-use** — the same tool that defends authorised assets can attack unauthorised ones. Mitigation: cryptographically-signed RoE, hard scope checks before every tool call, immutable audit log, strict legal-counsel sign-off.

**Limitations of this reference.** Some forward-leaning vendor names (Claude Opus 4.7, GPT-5.5) are stated per the project brief — the architectural reasoning does not depend on these specific versions. Coverage of AutoAttacker and proprietary Burp Suite Enterprise APIs is shallower than coverage of OSS tools. The PDPA discussion summarises the act's relevance; specific compliance counsel is out of scope.

---

## Sources

[1] Model Context Protocol — Specification (2025-06-18). https://modelcontextprotocol.io/specification/2025-06-18
[2] Linux Foundation — Agentic AI Foundation launch / MCP donation (Dec 2025). https://www.linuxfoundation.org/press/linux-foundation-launches-agentic-ai-foundation
[3] Anthropic — How we built our multi-agent research system. https://www.anthropic.com/engineering/multi-agent-research-system
[4] OpenAI — Agents SDK (Python). https://openai.github.io/openai-agents-python/
[5] OpenAI — Building agents (Responses API guide). https://platform.openai.com/docs/guides/agents
[6] Anthropic — Tool use overview. https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview
[7] Deng et al., PentestGPT, USENIX Security 2024 (Distinguished Artifact Award). https://www.usenix.org/conference/usenixsecurity24/presentation/deng
[8] HackingBuddyGPT — TU Wien / ipa-lab (GitHub). https://github.com/ipa-lab/hackingBuddyGPT
[9] Project Naptime — Google Project Zero blog. https://googleprojectzero.blogspot.com/2024/06/project-naptime.html
[10] Big Sleep — Google blog, July 2025 SQLite zero-day. https://blog.google/technology/safety-security/big-sleep-ai-vulnerability-discovery/
[11] AgentDojo — ETH Zurich + Invariant Labs benchmark. https://agentdojo.spylab.ai/
[12] Microsoft Security Copilot — Microsoft Learn. https://learn.microsoft.com/en-us/copilot/security/microsoft-security-copilot
[13] Nuclei — ProjectDiscovery documentation. https://docs.projectdiscovery.io/tools/nuclei/overview
[14] Trivy — Aqua Security (trivy.dev). https://trivy.dev/
[15] Prowler — multi-cloud security tool documentation. https://docs.prowler.com/
[16] OSV.dev — OpenSSF distributed vulnerability database. https://osv.dev/
[17] CISA — Known Exploited Vulnerabilities Catalog (BOD 22-01). https://www.cisa.gov/known-exploited-vulnerabilities-catalog
[18] FIRST — Exploit Prediction Scoring System (EPSS). https://www.first.org/epss/
[19] OWASP — Top 10 for LLM Applications 2025 (PDF v2025). https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
[20] OWASP GenAI Security Project — LLM Top 10 home. https://genai.owasp.org/llm-top-10/
[21] NIST — AI Risk Management Framework (AI 100-1). https://www.nist.gov/itl/ai-risk-management-framework
[22] NIST — AI 600-1 Generative AI Profile (PDF). https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
[23] CISA — Stakeholder-Specific Vulnerability Categorization (SSVC). https://www.cisa.gov/stakeholder-specific-vulnerability-categorization-ssvc
[24] FIRST — CVSS v4.0 Specification Document. https://www.first.org/cvss/specification-document
[25] NVD — CVSS v4.0 Official Support announcement. https://nvd.nist.gov/general/news/cvss-v4-0-official-support
[26] Northflank — Kata Containers vs Firecracker vs gVisor (Jan 2026). https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor
[27] SpecterOps — BloodHound CE Introduction. https://bloodhound.specterops.io/get-started/introduction
[28] PingCastle — Download / licensing. https://www.pingcastle.com/download/
[29] AWS Prescriptive Guidance — Amazon Inspector for vulnerability management. https://docs.aws.amazon.com/prescriptive-guidance/latest/vulnerability-management/amazon-inspector.html
[30] Microsoft Learn — Microsoft Sentinel data connectors. https://learn.microsoft.com/en-us/azure/sentinel/connect-data-sources
[31] Google Cloud — Security Command Center vulnerability findings. https://docs.cloud.google.com/security-command-center/docs/concepts-vulnerabilities-findings
[32] Google Cloud Blog — Security AI Workbench / Sec-PaLM (RSA 2023). https://cloud.google.com/blog/products/identity-security/rsa-google-cloud-security-ai-workbench-generative-ai
[33] Google Cloud — Gemini in Google SecOps documentation. https://docs.cloud.google.com/chronicle/docs/secops/gemini-secops
[34] OWASP ZAP — Automation Framework documentation. https://www.zaproxy.org/docs/automate/automation-framework/
[35] Thailand MDES — Personal Data Protection Act, B.E. 2562 (2019). https://mdes.go.th/law/detail/3577-Personal-Data-Protection-Act-B-E--2562--2019-
[36] MITRE — Caldera MCP plugin (GitHub). https://github.com/mitre/MCP
[37] MITRE Caldera — project home. https://caldera.mitre.org/
[38] Qualys — Understanding CVSS v4. https://blog.qualys.com/product-tech/2023/11/02/cvss-v4-is-now-live-and-what-do-you-need-to-know
[39] turingsecure — CVSS v4.0 changes from 3.1. https://turingsecure.com/blog/cvss-v4-scoring-system/
[40] Bits Lovers — AWS Inspector v2 risk-score formula. https://www.bitslovers.com/aws-inspector-guide/

*Word count: ~3,100 (excluding sources list). Access date for all URLs: 2026-04-30.*
