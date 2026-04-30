# Architecture Decision Records (ADRs)

The 8 binding ADRs are defined in `05-architecture.md` §5. This file tracks
**implementation-level** decisions made while building v0.1 in this repo.

## ADR-9 — Azure-managed deployment as v0.1 "customer-cloud" interpretation

**Date:** 2026-04-30
**Decision:** The first reference deployment is Azure-managed (AKS + managed services)
in resource group `AutoScan` of subscription `0fdda5f4-0853-4336-8f41-0370176387f5`.
The Helm chart in `infra/helm/autoscan` is portable to any K8s 1.30+ cluster, so the
on-prem path required by ADR-7 is preserved.
**Rationale:** Faster path to a working scanner; reuses managed Azure OpenAI for the
GPT specialist tier; Defender for Cloud + Sentinel give the AVS itself a verifiable
audit baseline (alignment with PRD §9.12).

## ADR-10 — Cosmos DB Gremlin instead of Neo4j Community for Phase-2 v0.1

**Date:** 2026-04-30
**Decision:** Use Cosmos DB with the Gremlin API for the Asset Graph in v0.1.
Neo4j-on-AKS is deferred to a benchmark in Phase-2 v0.2 (open question O-1 from PRD §10
will be resolved with concrete numbers).
**Rationale:** Managed, serverless billing, RBAC via AAD, no operator burden. The
graph traversal queries used by the Exploit-Reasoning agent map cleanly to Gremlin
`g.V().has(...).repeat(...).times(N)` patterns. If we hit modeling limits we will
reverse this decision in v0.2.

## ADR-11 — Azure OpenAI for the GPT tier; Anthropic API direct for the Claude tier

**Date:** 2026-04-30
**Decision:** GPT specialists call Azure OpenAI deployments (`gpt-4o`,
`gpt-4o-mini`, `o1-mini`). The orchestrator and exploit-reasoning agents call
Anthropic's API directly (no Azure equivalent at the time of writing).
**Rationale:** Required to honor ADR-2's vendor-diversity property. Anthropic API key
is stored in Key Vault and surfaced to AKS pods via the CSI Secrets Store driver.

## ADR-12 — gVisor as the v0.1 sandbox; Firecracker deferred

**Date:** 2026-04-30
**Decision:** AKS sandbox node pool runs the standard kernel; tool pods are scheduled
to a labeled pool (`workload=sandbox`) and configured for gVisor when the runtime
class is available. Firecracker microVM (preferred per ADR-3) requires KVM-capable
hosts which AKS does not currently expose; deferred to v0.2 with a custom node
image, or to the on-prem deployment shape.
**Rationale:** Keeps the sandbox boundary intact, accepts a weaker isolation
property than Firecracker (documented as gap G8). Pod security context, network
policies (Cilium), and network egress allowlists provide additional defense in depth.

## ADR-13 — RFC 3161 anchor authority is configurable

**Date:** 2026-04-30
**Decision:** `evidence-mcp` reads `RFC3161_TSA_URL` from env. v0.1 ships with
`https://freetsa.org/tsr` as a placeholder. Production deployments must override
with a Thai-aligned TSA (e.g. `digicert-tsa-th`) or multi-TSA fallback per gap G7.
