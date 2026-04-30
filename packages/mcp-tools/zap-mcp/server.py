"""zap-mcp — OWASP ZAP Automation Framework wrapper.

ZAP active scan IS potentially destructive (per build-spec §8). Marked
destructive=True so the OPA gate requires per-asset opt-in.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="zap-mcp", version="0.1.0")
ZAP_API = os.environ.get("ZAP_API_URL", "http://localhost:8090")
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "")


@server.tool(ToolSpec(
    name="mcp.zap.passiveScan",
    description="Spider + passive scan a target.",
    input_schema={
        "type": "object",
        "properties": {"target": {"type": "string"}},
        "required": ["target"],
    },
    category="webapp",
))
async def zap_passive(params):
    target = params["target"]
    async with httpx.AsyncClient(timeout=600) as c:
        r = await c.get(f"{ZAP_API}/JSON/spider/action/scan/",
                        params={"url": target, "apikey": ZAP_API_KEY})
        scan_id = r.json().get("scan")
        # Poll
        for _ in range(60):
            r = await c.get(f"{ZAP_API}/JSON/spider/view/status/",
                            params={"scanId": scan_id, "apikey": ZAP_API_KEY})
            if int(r.json().get("status", 0)) >= 100:
                break
            await asyncio.sleep(5)
        # Pull alerts
        r = await c.get(f"{ZAP_API}/JSON/core/view/alerts/",
                        params={"baseurl": target, "apikey": ZAP_API_KEY})
        return {"alerts": r.json().get("alerts", [])}


@server.tool(ToolSpec(
    name="mcp.zap.activeScan",
    description="ACTIVE web app scan — DESTRUCTIVE per build-spec §8. Requires per-asset opt-in.",
    input_schema={
        "type": "object",
        "properties": {"target": {"type": "string"}, "policy": {"type": "string"}},
        "required": ["target"],
    },
    category="webapp",
    destructive=True,
))
async def zap_active(params):
    target = params["target"]
    async with httpx.AsyncClient(timeout=3600) as c:
        r = await c.get(f"{ZAP_API}/JSON/ascan/action/scan/",
                        params={"url": target, "apikey": ZAP_API_KEY})
        scan_id = r.json().get("scan")
        for _ in range(720):
            r = await c.get(f"{ZAP_API}/JSON/ascan/view/status/",
                            params={"scanId": scan_id, "apikey": ZAP_API_KEY})
            if int(r.json().get("status", 0)) >= 100:
                break
            await asyncio.sleep(5)
        r = await c.get(f"{ZAP_API}/JSON/core/view/alerts/",
                        params={"baseurl": target, "apikey": ZAP_API_KEY})
        return {"alerts": r.json().get("alerts", [])}


app = server.app()
