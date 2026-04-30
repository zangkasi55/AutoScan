"""Minimal MCP-server scaffolding shared by all AutoScan MCP servers.

We use a lightweight HTTP/JSON-RPC 2.0 transport. The official
`@modelcontextprotocol/sdk` (TypeScript) and `mcp` (Python) packages
plug in here in Phase 2; this scaffold matches the JSON-RPC 2.0 wire
shape used by MCP so callers do not need to change.

Every server exposes:
  GET  /health
  GET  /metadata     → tool list + schemas
  POST /invoke       → JSON-RPC 2.0 method = tool name
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import httpx
from fastapi import FastAPI, HTTPException, Request

log = logging.getLogger("mcp")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

POLICY_MCP_URL = os.environ.get("POLICY_MCP_URL", "http://policy-mcp:8080")
EVIDENCE_MCP_URL = os.environ.get("EVIDENCE_MCP_URL", "http://evidence-mcp:8080")


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    destructive: bool = False
    category: str = "recon"
    handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None


@dataclass
class MCPServer:
    name: str
    version: str = "0.1.0"
    tools: dict[str, ToolSpec] = field(default_factory=dict)

    def tool(self, spec: ToolSpec):
        def decorator(fn: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]):
            spec.handler = fn
            self.tools[spec.name] = spec
            return fn
        return decorator

    def app(self) -> FastAPI:
        app = FastAPI(title=self.name, version=self.version)

        @app.get("/health")
        async def health():
            return {"status": "ok", "server": self.name, "version": self.version}

        @app.get("/metadata")
        async def metadata():
            return {
                "server": self.name,
                "version": self.version,
                "tools": [
                    {
                        "name": t.name, "description": t.description,
                        "input_schema": t.input_schema,
                        "destructive": t.destructive, "category": t.category,
                    } for t in self.tools.values()
                ],
            }

        @app.post("/invoke")
        async def invoke(req: Request):
            body = await req.json()
            method = body.get("method")
            params = body.get("params", {})
            req_id = body.get("id")
            tool = self.tools.get(method)
            if not tool:
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32601, "message": f"unknown tool {method}"}}

            policy_input = params.get("_policy_input")
            if policy_input is None:
                raise HTTPException(400, "missing _policy_input on invoke")
            decision = await _check_policy(policy_input, tool)
            if not decision.get("allow"):
                await _evidence_append(
                    scan_id=params.get("_scan_id"),
                    actor=f"mcp-server:{self.name}",
                    action=f"deny.{method}",
                    payload={"deny_reasons": decision.get("deny_reasons", []),
                             "params": _scrub(params)},
                    policy=decision,
                )
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32001, "message": "policy_denied",
                                  "data": decision.get("deny_reasons", [])}}

            t0 = time.perf_counter()
            try:
                result = await tool.handler(params)
                ok, err = True, None
            except Exception as e:
                log.exception("tool failed")
                result, ok, err = None, False, str(e)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            idx = await _evidence_append(
                scan_id=params.get("_scan_id"),
                actor=f"mcp-server:{self.name}",
                action=f"invoke.{method}",
                payload={"params": _scrub(params),
                         "result": result if ok else {"error": err},
                         "elapsed_ms": elapsed_ms, "ok": ok},
                policy=decision,
            )
            if not ok:
                return {"jsonrpc": "2.0", "id": req_id,
                        "error": {"code": -32000, "message": err}}
            return {"jsonrpc": "2.0", "id": req_id,
                    "result": {"data": result, "evidence_idx": idx, "elapsed_ms": elapsed_ms}}

        return app


def _scrub(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if not k.startswith("_")}


async def _check_policy(policy_input: dict[str, Any], tool: ToolSpec) -> dict[str, Any]:
    payload = {**policy_input, "tool_category": tool.category,
               "action_destructive": tool.destructive or policy_input.get("action_destructive", False)}
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post(f"{POLICY_MCP_URL}/decide", json=payload)
            return r.json()
    except Exception as e:
        log.warning("policy-mcp unreachable, FAIL CLOSED: %s", e)
        return {"allow": False, "deny_reasons": ["policy_engine_unreachable"]}


async def _evidence_append(scan_id, actor, action, payload, policy) -> int | None:
    if not scan_id:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post(f"{EVIDENCE_MCP_URL}/append",
                             json={"scan_id": scan_id, "actor": actor,
                                   "action": action, "payload": payload, "policy": policy})
            return r.json().get("idx")
    except Exception as e:
        log.warning("evidence-mcp unreachable: %s", e)
        return None
