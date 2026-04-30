"""policy-mcp — RoE authorization gate sidecar.

Wraps the OPA bundle (packages/policy-engine) and exposes a single endpoint
/decide that every other MCP server calls before executing a tool.

Fail-closed by design.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

import httpx
from fastapi import FastAPI

log = logging.getLogger("policy-mcp")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

OPA_URL = os.environ.get("OPA_URL", "http://localhost:8181")
OPA_DECISION_PATH = os.environ.get("OPA_DECISION", "v1/data/avs/authorize")

app = FastAPI(title="policy-mcp", version="0.1.0")


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(f"{OPA_URL}/health")
            r.raise_for_status()
        return {"status": "ok", "opa": "ok"}
    except Exception as e:
        return {"status": "degraded", "opa_error": str(e)}


@app.post("/decide")
async def decide(input_doc: dict):
    """Forward to OPA. Fail-closed on any error."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post(f"{OPA_URL}/{OPA_DECISION_PATH}", json={"input": input_doc})
            r.raise_for_status()
            data = r.json().get("result", {})
        return {
            "allow": bool(data.get("allow", False)),
            "deny_reasons": list(data.get("deny_reasons", [])),
            "input_summary": {
                "tool_category": input_doc.get("tool_category"),
                "destructive": input_doc.get("action_destructive", False),
                "target_id": (input_doc.get("target") or {}).get("id"),
            },
        }
    except Exception as e:
        log.error("OPA decision failed: %s", e)
        return {"allow": False, "deny_reasons": ["opa_unreachable"]}
