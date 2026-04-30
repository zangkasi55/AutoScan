"""nmap-mcp — MCP server wrapping Nmap.

Exposes:
  mcp.nmap.scan(target, ports?, scripts?) → parsed ports + services
  mcp.nmap.discover(cidr) → live hosts via -sn

Non-destructive by definition (default tool category = 'recon').
Sandboxing is provided by the surrounding pod (gVisor profile in production).
"""
from __future__ import annotations

import asyncio
import json
import shlex
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Make _common importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="nmap-mcp", version="0.1.0")


async def _run(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return proc.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def _parse_xml(xml_text: str) -> list[dict]:
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    hosts = []
    for h in root.findall("host"):
        addr_el = h.find("address")
        addr = addr_el.attrib.get("addr") if addr_el is not None else None
        status = (h.find("status") or {}).attrib.get("state") if h.find("status") is not None else None
        ports = []
        for p in h.findall(".//port"):
            svc = p.find("service")
            ports.append({
                "port": int(p.attrib["portid"]),
                "proto": p.attrib.get("protocol"),
                "state": (p.find("state") or {}).attrib.get("state") if p.find("state") is not None else None,
                "service": svc.attrib.get("name") if svc is not None else None,
                "product": svc.attrib.get("product") if svc is not None else None,
                "version": svc.attrib.get("version") if svc is not None else None,
            })
        hosts.append({"address": addr, "status": status, "ports": ports})
    return hosts


@server.tool(ToolSpec(
    name="mcp.nmap.scan",
    description="Run an nmap port scan with banner+service detection.",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string"},
            "ports": {"type": "string", "default": "1-1024"},
            "scripts": {"type": "string"},
            "timing": {"type": "integer", "minimum": 0, "maximum": 5, "default": 3},
        },
        "required": ["target"],
    },
    destructive=False,
    category="recon",
))
async def nmap_scan(params: dict) -> dict:
    target = params["target"]
    ports = params.get("ports", "1-1024")
    scripts = params.get("scripts")
    timing = params.get("timing", 3)
    cmd = ["nmap", "-Pn", "-sV", f"-T{timing}", "-p", ports, "-oX", "-"]
    if scripts:
        cmd.extend(["--script", scripts])
    cmd.append(target)
    rc, out, err = await _run(cmd, timeout=600)
    return {
        "command": shlex.join(cmd),
        "exit_code": rc,
        "stderr_tail": err[-512:],
        "hosts": _parse_xml(out),
    }


@server.tool(ToolSpec(
    name="mcp.nmap.discover",
    description="Live-host discovery on a CIDR (nmap -sn).",
    input_schema={
        "type": "object",
        "properties": {"cidr": {"type": "string"}},
        "required": ["cidr"],
    },
    destructive=False,
    category="recon",
))
async def nmap_discover(params: dict) -> dict:
    cidr = params["cidr"]
    cmd = ["nmap", "-sn", "-oX", "-", cidr]
    rc, out, err = await _run(cmd, timeout=300)
    return {"exit_code": rc, "hosts": _parse_xml(out), "stderr_tail": err[-512:]}


app = server.app()
