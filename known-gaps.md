# Known gaps · AVS Phase 1

Curated by PM. Each entry: gap → why it matters → who owns the resolution → target phase.

| # | Gap | Why it matters | Owner | Target |
|---|-----|----------------|-------|--------|
| G1 | i18n-lint build-time enforcement of EN+TH contract is not yet implemented; bilingual coverage in Phase 1 is manual. | If a single Report-Writer call ships English-only narrative, it breaks our regulator-pack value prop with Thai customers. | Developer | Phase 2 |
| G2 | Critic agent isolation — independent context must be enforced at runtime, not by convention. | If the Critic shares context with the Vuln agent that produced a finding, "independent corroboration" becomes circular and FP rate claims are invalidated. | Architect → Developer | Phase 2 |
| G3 | Multi-vendor LLM (Anthropic + OpenAI) requires a provider-failure runbook. | Cross-vendor diversity is a stated ADR; operational playbook for vendor outages (rate-limit, billing, service incident) is not yet documented. | PM + Architect | Phase 2 |
| G4 | AI / LLM-app probing (OWASP LLM Top 10 active testing) deferred to v1.1. | Enterprises increasingly want this; Mindgard / RunSybil are competing on it. v0.1 covers the substrate (sandboxing, evidence) but not the probes. | PM | v1.1 (post-Phase 3) |
| G5 | Per-asset destructive opt-in state machine is described in PRD but not fully visualized in Phase 1 mockups. | Risk of ambiguity at sales demo; need clear consent flow per asset. | UX + Developer | Phase 2 v0.2 |
| G6 | Token/latency telemetry shown statically in mockups. | No real OTel wiring yet; production must emit traces from every agent call. | Developer | Phase 2 |
| G7 | RFC 3161 TSA dependency on `digicert-tsa-th` (single TSA). | Single point of trust dependency; should support multi-TSA fallback. | Architect | Phase 2 v0.2 |
| G8 | Sandbox boundary for Exploit-Reasoning replay (Firecracker microVM) requires customer infra (KVM-capable hosts). | Some enterprises will not have KVM available for AVS workers; gVisor fallback noted but not specced. | Architect | Phase 2 |
| G9 | Pricing / packaging / GTM intentionally excluded by user direction. | Will be needed before market entry; deferred per user decision. | (deferred) | post-Phase 1 |
| G10 | The mockup demo tenant is hard-coded ("SCB Tech"). | Phase 2 must drive tenant info from auth context. | Developer | Phase 2 |
