"""nuclei-mcp — MCP server wrapping ProjectDiscovery Nuclei (templated detection).

Templates are pinned to a known commit by the container image; runtime never
fetches templates from the network unless the operator opts in.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="nuclei-mcp", version="0.1.0")
TEMPLATES_DIR = os.environ.get("NUCLEI_TEMPLATES_DIR", "/opt/nuclei-templates")


async def _run(cmd: list[str], timeout: int = 600) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return proc.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def _parse_jsonl(text: str) -> list[dict]:
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


@server.tool(ToolSpec(
    name="mcp.nuclei.run",
    description="Run nuclei against a target URL or list with pinned templates.",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "severity": {"type": "string", "default": "low,medium,high,critical"},
            "rate_limit": {"type": "integer", "default": 50},
        },
        "required": ["target"],
    },
    destructive=False,
    category="cve",
))
async def nuclei_run(params: dict) -> dict:
    target = params["target"]
    tags = params.get("tags") or []
    severity = params.get("severity", "low,medium,high,critical")
    rate = params.get("rate_limit", 50)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as out_f:
        out_path = out_f.name
    cmd = [
        "nuclei", "-u", target, "-jsonl", "-o", out_path,
        "-severity", severity, "-rate-limit", str(rate),
        "-templates", TEMPLATES_DIR, "-disable-update-check", "-silent",
    ]
    if tags:
        cmd.extend(["-tags", ",".join(tags)])
    rc, _, err = await _run(cmd, timeout=900)
    try:
        body = open(out_path, "r", encoding="utf-8", errors="replace").read()
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass
    findings = _parse_jsonl(body)
    return {
        "exit_code": rc,
        "stderr_tail": err[-512:],
        "finding_count": len(findings),
        "findings": findings,
    }


app = server.app()
