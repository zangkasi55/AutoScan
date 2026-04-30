# AVS Authorization Gate (OPA / Rego)

This bundle is the runtime authorization gate. **Every MCP tool call** —
without exception — passes through `data.avs.authorize.allow` before
execution. Out-of-scope = hard fail.

Per ADR-3 / build spec §4.2.

## Build

```bash
opa test .              # run rego unit tests
opa build -b . -o bundle.tar.gz
```

## Decision contract

Input shape (validated by `policy-mcp` adapter):

```json
{
  "now": "2026-04-30T12:34:56Z",
  "tool_category": "recon",          // recon|cve|webapp|ad|chain|dos
  "action_destructive": false,
  "target": {
    "id": "10.0.0.5:443",
    "kind": "host|cidr|cloud_account|domain",
    "address": "10.0.0.5",
    "cidr_in_scope": true,
    "cidr_excluded": false
  },
  "roe": {
    "id": "...uuid...",
    "test_categories": ["recon","cve"],
    "starts_at": "2026-04-30T00:00:00Z",
    "ends_at":   "2026-07-30T00:00:00Z",
    "no_go_windows": [{"start":"02:00","end":"04:00","reason":"backup"}],
    "destructive_opt_ins": [{"asset":"10.0.0.5:443","allow":true,"justification":"..."}]
  }
}
```

Output: `{"allow": bool, "deny_reasons": [..]}`.
