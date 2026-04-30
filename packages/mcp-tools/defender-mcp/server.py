"""defender-mcp — read findings from Microsoft Defender for Cloud (Azure)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="defender-mcp", version="0.1.0")


async def _aad_token():
    """Get a Defender ARM token via workload identity / managed identity."""
    from azure.identity.aio import DefaultAzureCredential
    cred = DefaultAzureCredential()
    tok = await cred.get_token("https://management.azure.com/.default")
    return tok.token


@server.tool(ToolSpec(
    name="mcp.defender.recommendations",
    description="List Defender for Cloud recommendations for a subscription.",
    input_schema={"type": "object", "properties": {"subscription_id": {"type": "string"}},
                  "required": ["subscription_id"]},
    category="cve",
))
async def recommendations(params):
    sub = params["subscription_id"]
    tok = await _aad_token()
    url = f"https://management.azure.com/subscriptions/{sub}/providers/Microsoft.Security/assessments?api-version=2020-01-01"
    async with httpx.AsyncClient(timeout=120, headers={"Authorization": f"Bearer {tok}"}) as c:
        items = []
        next_url = url
        while next_url:
            r = await c.get(next_url)
            r.raise_for_status()
            d = r.json()
            items.extend(d.get("value", []))
            next_url = d.get("nextLink")
    return {"count": len(items), "assessments": items}


@server.tool(ToolSpec(
    name="mcp.defender.alerts",
    description="List Defender for Cloud alerts for a subscription.",
    input_schema={"type": "object", "properties": {"subscription_id": {"type": "string"}},
                  "required": ["subscription_id"]},
    category="cve",
))
async def alerts(params):
    sub = params["subscription_id"]
    tok = await _aad_token()
    url = f"https://management.azure.com/subscriptions/{sub}/providers/Microsoft.Security/alerts?api-version=2022-01-01"
    async with httpx.AsyncClient(timeout=120, headers={"Authorization": f"Bearer {tok}"}) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()


app = server.app()
