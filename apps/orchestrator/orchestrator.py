"""Orchestrator (planner) — Claude Opus by default.

Loads the signed RoE → asks the LLM to produce a JSON plan → validates the
plan does not exceed the RoE scope → publishes the plan and dispatches phases
to the agent-runner workers.
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.mcp_tools.model_router_mcp import router  # type: ignore  # noqa: E402

log = logging.getLogger("orchestrator")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

ROLES_PATH = Path(__file__).resolve().parents[2] / "packages" / "agent-roles" / "roles.yaml"


def _load_roles() -> dict[str, Any]:
    return yaml.safe_load(ROLES_PATH.read_text())


async def plan_scan(roe: dict[str, Any]) -> dict[str, Any]:
    roles = _load_roles()
    system = roles["orchestrator"]["system_prompt"]
    user = (
        "Plan a scan. The signed RoE document below is the authoritative scope. "
        "Output ONLY the JSON plan described in the system prompt.\n\n"
        f"RoE:\n{json.dumps(roe, ensure_ascii=False, indent=2)}"
    )
    res = await router.complete(
        role="orchestrator",
        system=system,
        user=user,
        isolation_token="orchestrator-planning",
        max_tokens=8000,
        temperature=0.1,
    )
    plan = _parse_json(res.text)
    _validate_plan_within_scope(plan, roe)
    return plan


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text)


def _validate_plan_within_scope(plan: dict[str, Any], roe: dict[str, Any]) -> None:
    """Reject plans that target anything outside the signed RoE.

    Defense in depth — the OPA gate is the authoritative runtime barrier.
    """
    in_cidrs = [ipaddress.ip_network(c, strict=False) for c in roe["scope"]["cidrs"]]
    in_hosts = set(roe["scope"]["hosts"])
    excluded_cidrs = [ipaddress.ip_network(c, strict=False) for c in roe["exclusions"]["cidrs"]]
    excluded_hosts = set(roe["exclusions"]["hosts"])

    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            target = step.get("target")
            if not target:
                continue
            if target in excluded_hosts:
                raise ValueError(f"plan targets excluded host: {target}")

            host = target.split(":")[0]
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                # treat as hostname
                if target not in in_hosts and host not in in_hosts:
                    raise ValueError(f"plan targets out-of-scope hostname: {target}")
                continue
            if any(ip in c for c in excluded_cidrs):
                raise ValueError(f"plan targets excluded cidr: {target}")
            if not any(ip in c for c in in_cidrs):
                raise ValueError(f"plan targets out-of-scope: {target}")
