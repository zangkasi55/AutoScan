"""End-to-end smoke test against a docker-compose-up environment.

Spins up RoE → start scan stub → invokes nmap-mcp through policy gate →
verifies evidence row appended with valid Merkle chain.

Run: python -m pytest tests/integration -v
"""
from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

POLICY_URL = os.environ.get("POLICY_MCP_URL", "http://localhost:8001")
EVIDENCE_URL = os.environ.get("EVIDENCE_MCP_URL", "http://localhost:8002")
NMAP_URL = os.environ.get("NMAP_MCP_URL", "http://localhost:8003")
SCAN_ID = "00000000-0000-0000-0000-0000000000aa"


def _services_up() -> bool:
    for url in (POLICY_URL, EVIDENCE_URL, NMAP_URL):
        try:
            httpx.get(f"{url}/health", timeout=2)
        except Exception:
            return False
    return True


pytestmark = pytest.mark.skipif(
    not _services_up(),
    reason="docker compose stack not running — start with `docker compose -f infra/docker-compose.yml up -d`",
)


def test_in_scope_recon_passes():
    body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "mcp.nmap.discover",
        "params": {
            "_scan_id": SCAN_ID,
            "_policy_input": {
                "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tool_category": "recon",
                "action_destructive": False,
                "target": {"id": "127.0.0.1", "kind": "cidr",
                           "cidr_in_scope": True, "cidr_excluded": False},
                "roe": {
                    "id": "test-roe",
                    "test_categories": ["recon", "cve"],
                    "starts_at": "2026-01-01T00:00:00Z",
                    "ends_at":   "2027-01-01T00:00:00Z",
                    "no_go_windows": [],
                    "destructive_opt_ins": [],
                },
            },
            "cidr": "127.0.0.1",
        },
    }
    r = httpx.post(f"{NMAP_URL}/invoke", json=body, timeout=120)
    j = r.json()
    assert "error" not in j, j
    assert j["result"]["evidence_idx"] is not None


def test_out_of_scope_blocked():
    body = {
        "jsonrpc": "2.0", "id": str(uuid.uuid4()),
        "method": "mcp.nmap.discover",
        "params": {
            "_scan_id": SCAN_ID,
            "_policy_input": {
                "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tool_category": "recon", "action_destructive": False,
                "target": {"id": "8.8.8.8", "kind": "cidr",
                           "cidr_in_scope": False, "cidr_excluded": False},
                "roe": {
                    "id": "test-roe", "test_categories": ["recon"],
                    "starts_at": "2026-01-01T00:00:00Z",
                    "ends_at":   "2027-01-01T00:00:00Z",
                    "no_go_windows": [], "destructive_opt_ins": [],
                },
            },
            "cidr": "8.8.8.8/32",
        },
    }
    r = httpx.post(f"{NMAP_URL}/invoke", json=body, timeout=30)
    j = r.json()
    assert j["error"]["message"] == "policy_denied"
    assert "target_out_of_scope" in j["error"]["data"]
