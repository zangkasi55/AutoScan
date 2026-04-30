# AutoScan Operations Runbook

## On-call essentials

### "Scans aren't starting"
1. Check `policy-mcp` health: `kubectl exec deploy/autoscan-policy-mcp -- curl -s localhost:8080/health`
   - If `opa_unreachable` — restart the pod (OPA is co-located).
2. Verify the RoE is signed (`status='active'`) in `roe_documents`.
3. Check `evidence-mcp` Postgres connectivity.

### "Scope-deviation alerts"
- This is a hard requirement (PRD §9). Investigate the audit log:
  ```sql
  SELECT * FROM evidence WHERE action LIKE 'deny.%' ORDER BY idx DESC LIMIT 50;
  ```
- Confirm the planner output did not exceed RoE (`apps/orchestrator/orchestrator.py::_validate_plan_within_scope`).

### "Critic disagrees with Vuln"
- Expected behavior. The Critic suppresses promotion. Check `findings.critic_verdict`.
- If FP rate creeps above 5%, retrain the Vuln prompt (versioned in
  `packages/agent-roles/roles.yaml`).

### "LLM vendor outage"
- model-router-mcp falls back automatically (primary → fallback once).
- If both vendors are down, scans pause; orchestrator will not auto-resume.
- Manual override via `kubectl set env deploy/autoscan-orchestrator FORCE_VENDOR=openai`.

### "Evidence ledger Merkle root mismatch"
- This is a **SEV-1**. Stop all scans for the tenant.
- Recompute root from `evidence` table; compare to last `ledger_anchors` entry.
- If divergent, the database has been tampered with (or there is a bug). Open
  incident; restore from backup; rotate KMS keys.

## Routine ops

- **Anchor cron** — runs every 15 min, batches new evidence rows into a Merkle
  root and submits to the configured TSA. Failures alert via App Insights.
- **Defender for Cloud** — review weekly: Defender → Recommendations.
- **Sentinel** — analytic rules onboarded by Bicep; tune thresholds as scan
  volume grows.
- **Key Vault rotation** — Postgres admin secret rotates manually for now;
  automation is on the v0.2 roadmap.

## Kill switch

```bash
# Pause all scans
kubectl scale deploy autoscan-orchestrator --replicas=0
kubectl scale deploy autoscan-agent-runner --replicas=0
# MCP servers can stay up — they will simply not be called.
```

Per PRD §9.10 the kill switch must abort within 5 seconds. Helm scale satisfies
this; the operator-facing UI button is wired to the same kubectl scale path.
