# AutoScan / Sentry-AI — Roadmap (post-v0.1)

| Wave | Scope |
|------|-------|
| **v0.1.1** | Wire ZAP active-scan with sidecar pattern; finalize WebAuthn signing; add Sentinel analytic rules import to Bicep; AKS gVisor RuntimeClass; Front Door → AKS Ingress origin wiring. |
| **v0.2** | All 20 MCP servers: ScoutSuite, BloodHound CE, AzureHound, Inspector v2, GCP SCC, OSV, GHSA, Hashcat (gated), Hydra (gated). Multi-TSA fallback (gap G7). Critic isolation enforced at K8s NetworkPolicy + separate ServiceAccount. Firecracker microVM via custom node image (gap G8). |
| **v0.3** | Asset graph migration benchmark Cosmos vs Neo4j (open issue O-1). Replay sandbox for Exploit-Reasoning corroboration. PDPA evidence-pack assembler with regulator-pack templates. CycloneDX/STIX export. Diff-aware re-scan jobs. |
| **v1.0** | Multi-tenant SaaS (deferred from v0.1 ADR-7). Multi-region. Customer-managed keys via HSM. Brand-customizable per tenant. |
| **v1.1** | OWASP LLM Top-10 active probes (MITRE ATLAS). Mindgard / RunSybil-class capability. Bug-bounty *outbound* pipeline (curated submission, never auto). |

## Open issues mapped from PRD §10

| # | Status |
|---|--------|
| O-1 (graph backing store) | Cosmos Gremlin in v0.1 (ADR-10). Benchmark vs Neo4j in v0.2. |
| O-2 (evidence ledger backing) | Append-only PG + Merkle in v0.1 (ADR-4). |
| O-3 (LLM-app probes) | v1.1 confirmed. |
| O-4 (Burp license) | Defer. ZAP only in v0.1 / v0.2. |
| O-5 (hosted vs on-prem) | Customer-cloud (Azure) in v0.1 reference; Helm portable to on-prem. |
