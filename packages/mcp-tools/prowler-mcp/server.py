"""prowler-mcp — Multi-cloud configuration auditor (Prowler v4)."""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="prowler-mcp", version="0.1.0")


async def _run(cmd: list[str], timeout: int = 1800) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return proc.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


@server.tool(ToolSpec(
    name="mcp.prowler.aws",
    description="Run Prowler against an AWS account (read-only).",
    input_schema={
        "type": "object",
        "properties": {
            "account_id": {"type": "string"},
            "regions": {"type": "array", "items": {"type": "string"}},
            "checks": {"type": "array", "items": {"type": "string"}},
            "severity": {"type": "string", "default": "low,medium,high,critical"},
        },
        "required": ["account_id"],
    },
    destructive=False,
    category="cve",
))
async def prowler_aws(params: dict) -> dict:
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        cmd = ["prowler", "aws", "-M", "json-asff", "-o", str(out_dir), "-q",
               "--severity", params.get("severity", "low,medium,high,critical")]
        if params.get("regions"):
            cmd.extend(["-f", *params["regions"]])
        if params.get("checks"):
            cmd.extend(["-c", *params["checks"]])
        rc, out, err = await _run(cmd, timeout=3600)
        findings = []
        for f in out_dir.glob("*.json*"):
            try:
                data = json.loads(f.read_text())
                findings.extend(data if isinstance(data, list) else [data])
            except json.JSONDecodeError:
                continue
    return {
        "exit_code": rc, "stderr_tail": err[-512:],
        "finding_count": len(findings), "findings": findings,
    }


@server.tool(ToolSpec(
    name="mcp.prowler.azure",
    description="Run Prowler against an Azure subscription (read-only).",
    input_schema={
        "type": "object",
        "properties": {"subscription_id": {"type": "string"}},
        "required": ["subscription_id"],
    },
    destructive=False,
    category="cve",
))
async def prowler_azure(params: dict) -> dict:
    sub = params["subscription_id"]
    with tempfile.TemporaryDirectory() as td:
        cmd = ["prowler", "azure", "--az-cli-auth", "--subscription-ids", sub,
               "-M", "json-asff", "-o", td, "-q"]
        rc, _, err = await _run(cmd, timeout=3600)
        findings = []
        for f in Path(td).glob("*.json*"):
            try:
                data = json.loads(f.read_text())
                findings.extend(data if isinstance(data, list) else [data])
            except json.JSONDecodeError:
                continue
    return {"exit_code": rc, "stderr_tail": err[-512:], "findings": findings}


app = server.app()
