"""kev-mcp + epss-mcp + nvd-mcp combined — vuln-intel data lookups (read-only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import asyncpg
from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common.mcp_base import MCPServer, ToolSpec  # noqa: E402

server = MCPServer(name="kev-mcp", version="0.1.0")
DB_URL = os.environ.get("VULN_INTEL_DB_URL", "")
_pool: asyncpg.Pool | None = None


async def _ensure_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)


@server.tool(ToolSpec(
    name="mcp.kev.lookup",
    description="Is the given CVE in CISA KEV?",
    input_schema={"type": "object", "properties": {"cve_id": {"type": "string"}},
                  "required": ["cve_id"]},
    category="recon",
))
async def kev_lookup(params):
    await _ensure_pool()
    async with _pool.acquire() as c:
        r = await c.fetchrow("SELECT * FROM vi_kev WHERE cve_id = $1", params["cve_id"])
    return {"in_kev": r is not None, "entry": dict(r) if r else None}


@server.tool(ToolSpec(
    name="mcp.epss.score",
    description="Get the latest EPSS score for a CVE.",
    input_schema={"type": "object", "properties": {"cve_id": {"type": "string"}},
                  "required": ["cve_id"]},
    category="recon",
))
async def epss_score(params):
    await _ensure_pool()
    async with _pool.acquire() as c:
        r = await c.fetchrow("SELECT cve_id, epss, percentile, scored_at FROM vi_epss WHERE cve_id = $1", params["cve_id"])
    return dict(r) if r else {"cve_id": params["cve_id"], "epss": None}


@server.tool(ToolSpec(
    name="mcp.nvd.lookup",
    description="Get NVD record (description, CVSS, references) for a CVE.",
    input_schema={"type": "object", "properties": {"cve_id": {"type": "string"}},
                  "required": ["cve_id"]},
    category="recon",
))
async def nvd_lookup(params):
    await _ensure_pool()
    async with _pool.acquire() as c:
        r = await c.fetchrow("SELECT * FROM vi_cve WHERE cve_id = $1", params["cve_id"])
    return dict(r) if r else None


@server.tool(ToolSpec(
    name="mcp.vi.batch_enrich",
    description="Bulk enrich a list of CVE ids with KEV/EPSS/CVSS in one call.",
    input_schema={"type": "object", "properties": {"cve_ids": {"type": "array", "items": {"type": "string"}}},
                  "required": ["cve_ids"]},
    category="recon",
))
async def batch_enrich(params):
    cves = params["cve_ids"]
    await _ensure_pool()
    async with _pool.acquire() as c:
        rows = await c.fetch(
            """SELECT v.cve_id,
                      v.cvss40_score, v.cvss31_score,
                      e.epss, e.percentile,
                      (k.cve_id IS NOT NULL) AS in_kev
               FROM unnest($1::text[]) AS u(cve_id)
               LEFT JOIN vi_cve v  ON v.cve_id = u.cve_id
               LEFT JOIN vi_epss e ON e.cve_id = u.cve_id
               LEFT JOIN vi_kev k  ON k.cve_id = u.cve_id""",
            cves,
        )
    return {"results": [dict(r) for r in rows]}


app = server.app()
