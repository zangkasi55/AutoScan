"""trivy-mcp — Trivy filesystem / image / IaC / SBOM scanner."""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="trivy-mcp", version="0.1.0")


async def _run(cmd, timeout=900):
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
    name="mcp.trivy.image",
    description="Scan a container image for vulnerabilities and misconfigs.",
    input_schema={
        "type": "object",
        "properties": {
            "image": {"type": "string"},
            "severity": {"type": "string", "default": "HIGH,CRITICAL"},
        },
        "required": ["image"],
    },
    category="cve",
))
async def trivy_image(params):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        out_path = f.name
    cmd = ["trivy", "image", "--quiet", "--format", "json", "--output", out_path,
           "--severity", params.get("severity", "HIGH,CRITICAL"), params["image"]]
    rc, _, err = await _run(cmd)
    try:
        data = json.loads(Path(out_path).read_text())
    except Exception:
        data = {}
    finally:
        Path(out_path).unlink(missing_ok=True)
    return {"exit_code": rc, "stderr_tail": err.decode(errors="replace")[-512:],
            "results": data.get("Results", []), "schema": data.get("SchemaVersion")}


@server.tool(ToolSpec(
    name="mcp.trivy.fs",
    description="Filesystem scan (SCA + IaC + secrets).",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "scanners": {"type": "string", "default": "vuln,misconfig,secret"},
        },
        "required": ["path"],
    },
    category="cve",
))
async def trivy_fs(params):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        out_path = f.name
    cmd = ["trivy", "fs", "--quiet", "--format", "json", "--output", out_path,
           "--scanners", params.get("scanners", "vuln,misconfig,secret"), params["path"]]
    rc, _, err = await _run(cmd)
    try:
        data = json.loads(Path(out_path).read_text())
    except Exception:
        data = {}
    finally:
        Path(out_path).unlink(missing_ok=True)
    return {"exit_code": rc, "results": data.get("Results", [])}


@server.tool(ToolSpec(
    name="mcp.trivy.sbom",
    description="Generate CycloneDX SBOM for an image or directory.",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string"},
            "kind": {"type": "string", "enum": ["image", "fs"], "default": "image"},
        },
        "required": ["target"],
    },
    category="recon",
))
async def trivy_sbom(params):
    sub = "image" if params.get("kind", "image") == "image" else "fs"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        out_path = f.name
    cmd = ["trivy", sub, "--quiet", "--format", "cyclonedx", "--output", out_path, params["target"]]
    rc, _, err = await _run(cmd)
    sbom = Path(out_path).read_text() if Path(out_path).exists() else ""
    Path(out_path).unlink(missing_ok=True)
    return {"exit_code": rc, "sbom_cyclonedx": sbom}


app = server.app()
