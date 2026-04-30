"""Specialist agent runner.

Each specialist (recon, vuln, exploit_reasoning, report_writer) is an instance
of `SpecialistAgent`. The Critic is special — see critic.py.

Specialists call MCP servers (nmap-mcp, nuclei-mcp, prowler-mcp, etc) via
HTTP/JSON-RPC; every call is gated by policy-mcp + recorded in evidence-mcp.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.mcp_tools.model_router_mcp import router  # type: ignore  # noqa: E402

log = logging.getLogger("agent-runner")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

ROLES_PATH = Path(__file__).resolve().parents[2] / "packages" / "agent-roles" / "roles.yaml"
ROLES = yaml.safe_load(ROLES_PATH.read_text())

# MCP server endpoints (overridable by Helm values).
MCP_ENDPOINTS = {
    "mcp.nmap.scan": os.environ.get("NMAP_MCP_URL", "http://nmap-mcp:8080"),
    "mcp.nmap.discover": os.environ.get("NMAP_MCP_URL", "http://nmap-mcp:8080"),
    "mcp.nuclei.run": os.environ.get("NUCLEI_MCP_URL", "http://nuclei-mcp:8080"),
    "mcp.prowler.aws": os.environ.get("PROWLER_MCP_URL", "http://prowler-mcp:8080"),
    "mcp.prowler.azure": os.environ.get("PROWLER_MCP_URL", "http://prowler-mcp:8080"),
}


@dataclass
class SpecialistAgent:
    role: str
    scan_id: str
    roe: dict[str, Any]

    async def run_step(self, step: dict[str, Any]) -> dict[str, Any]:
        """Execute one plan step against an MCP tool with full gating + evidence."""
        tool = step["tool"]
        target = step["target"]
        endpoint = MCP_ENDPOINTS.get(tool)
        if not endpoint:
            return {"ok": False, "error": f"no MCP endpoint for {tool}"}

        # Pre-compute the policy-input. The MCP server *also* checks; this is
        # defense in depth.
        policy_input = self._policy_input_for(target, step)
        body = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": tool,
            "params": {
                "_policy_input": policy_input,
                "_scan_id": self.scan_id,
                "target": target,
                **(step.get("args") or {}),
            },
        }
        async with httpx.AsyncClient(timeout=900) as c:
            r = await c.post(f"{endpoint}/invoke", json=body)
            r.raise_for_status()
            return r.json()

    def _policy_input_for(self, target: str, step: dict[str, Any]) -> dict[str, Any]:
        return {
            "now": _now_iso(),
            "tool_category": step.get("category", _category_for_role(self.role)),
            "action_destructive": bool(step.get("destructive", False)),
            "target": {
                "id": target,
                "kind": "host",
                "cidr_in_scope": True,    # the orchestrator pre-validated; OPA re-checks
                "cidr_excluded": False,
                "address": target.split(":")[0],
            },
            "roe": {
                "id": self.roe.get("id"),
                "test_categories": self.roe.get("testCategories", []),
                "starts_at": self.roe.get("timeWindow", {}).get("startsAt"),
                "ends_at": self.roe.get("timeWindow", {}).get("endsAt"),
                "no_go_windows": self.roe.get("timeWindow", {}).get("noGoWindows", []),
                "destructive_opt_ins": self.roe.get("destructiveOptIns", []),
            },
        }


def _category_for_role(role: str) -> str:
    return {
        "recon": "recon", "vuln": "cve", "exploit_reasoning": "chain",
        "report_writer": "recon", "critic": "recon",
    }.get(role, "recon")


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
