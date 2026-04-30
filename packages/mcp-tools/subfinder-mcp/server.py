"""subfinder-mcp + httpx-mcp combined — ProjectDiscovery passive subdomain discovery and HTTP probing."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="subfinder-mcp", version="0.1.0")


async def _run(cmd, timeout=300):
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, b"", b"timeout"
    return proc.returncode or 0, out, err


@server.tool(ToolSpec(
    name="mcp.subfinder.run",
    description="Passive subdomain enumeration.",
    input_schema={
        "type": "object",
        "properties": {"domain": {"type": "string"}},
        "required": ["domain"],
    },
    category="recon",
))
async def subfinder_run(params):
    cmd = ["subfinder", "-d", params["domain"], "-silent", "-json"]
    rc, out, err = await _run(cmd)
    domains = []
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            domains.append(json.loads(line))
        except json.JSONDecodeError:
            domains.append({"host": line})
    return {"exit_code": rc, "count": len(domains), "results": domains}


@server.tool(ToolSpec(
    name="mcp.httpx.probe",
    description="HTTP probing — title, status, tech, TLS.",
    input_schema={
        "type": "object",
        "properties": {
            "targets": {"type": "array", "items": {"type": "string"}},
            "ports": {"type": "string"},
        },
        "required": ["targets"],
    },
    category="recon",
))
async def httpx_probe(params):
    targets = "\n".join(params["targets"]).encode()
    cmd = ["httpx", "-silent", "-json", "-tech-detect", "-title", "-status-code"]
    if params.get("ports"):
        cmd += ["-ports", params["ports"]]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate(targets)
    results = []
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"exit_code": proc.returncode or 0, "count": len(results), "results": results}


app = server.app()
