"""evidence-mcp — Append-only ledger writer.

All writes go through evidence_append() (Postgres function). Input payloads
are redacted *before* persistence per build-spec §5.2 (PDPA contract).

Public endpoints:
  POST /append      — { scan_id, actor, action, payload, blob_uri?, policy } → { idx }
  GET  /by_scan/{id}?since=N&limit=N
  GET  /merkle/{id}                — current Merkle root + last anchored root
  POST /anchor/{id}                — submit current root to RFC 3161 TSA (TODO: live impl)
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path

import asyncpg
from fastapi import FastAPI, HTTPException

# Make the redactor importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "redactor"))
from redactor import redact_json  # type: ignore  # noqa: E402

log = logging.getLogger("evidence-mcp")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

DB_URL = os.environ.get("EVIDENCE_DB_URL", "postgres://avsadmin:avsadmin@postgres:5432/evidence?sslmode=require")
TSA_URL = os.environ.get("RFC3161_TSA_URL", "https://freetsa.org/tsr")  # placeholder; configurable

app = FastAPI(title="evidence-mcp", version="0.1.0")
_pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def _start():
    global _pool
    _pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=10)


@app.on_event("shutdown")
async def _stop():
    if _pool:
        await _pool.close()


@app.get("/health")
async def health():
    if not _pool:
        return {"status": "starting"}
    try:
        async with _pool.acquire() as c:
            v = await c.fetchval("SELECT 1")
        return {"status": "ok", "db": v == 1}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.post("/append")
async def append(body: dict):
    if not _pool:
        raise HTTPException(503, "db not ready")
    scan_id = body.get("scan_id")
    actor = body.get("actor")
    action = body.get("action")
    payload = body.get("payload") or {}
    blob_uri = body.get("blob_uri")
    policy = body.get("policy") or {}
    if not (scan_id and actor and action):
        raise HTTPException(400, "scan_id, actor, action required")

    redacted = redact_json(payload)
    async with _pool.acquire() as c:
        idx = await c.fetchval(
            "SELECT evidence_append($1::uuid, $2, $3, $4::jsonb, $5, $6::jsonb)",
            scan_id, actor, action, _to_json(redacted), blob_uri, _to_json(policy),
        )
    return {"idx": idx}


@app.get("/by_scan/{scan_id}")
async def by_scan(scan_id: str, since: int = 0, limit: int = 200):
    if not _pool:
        raise HTTPException(503, "db not ready")
    async with _pool.acquire() as c:
        rows = await c.fetch(
            "SELECT idx, actor, action, payload_blob, encode(parent_hash,'hex') parent_hash, "
            "encode(leaf_hash,'hex') leaf_hash, created_at FROM evidence "
            "WHERE scan_id = $1 AND idx > $2 ORDER BY idx LIMIT $3",
            scan_id, since, min(limit, 1000),
        )
    return [dict(r) for r in rows]


@app.get("/merkle/{scan_id}")
async def merkle(scan_id: str):
    if not _pool:
        raise HTTPException(503, "db not ready")
    async with _pool.acquire() as c:
        rows = await c.fetch(
            "SELECT leaf_hash FROM evidence WHERE scan_id = $1 ORDER BY idx", scan_id,
        )
        last_anchor = await c.fetchrow(
            "SELECT * FROM ledger_anchors WHERE scan_id = $1 ORDER BY anchor_id DESC LIMIT 1",
            scan_id,
        )
    leaves = [r["leaf_hash"] for r in rows]
    root = _merkle_root(leaves)
    return {
        "leaves": len(leaves),
        "merkle_root": root.hex() if root else None,
        "last_anchored": (
            {
                "from_idx": last_anchor["from_idx"],
                "to_idx": last_anchor["to_idx"],
                "merkle_root": last_anchor["merkle_root"].hex(),
                "tsa_authority": last_anchor["tsa_authority"],
                "anchored_at": str(last_anchor["anchored_at"]),
            }
            if last_anchor else None
        ),
    }


def _merkle_root(leaves: list[bytes]) -> bytes | None:
    if not leaves:
        return None
    layer = list(leaves)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i + 1] if i + 1 < len(layer) else a
            nxt.append(hashlib.sha256(a + b).digest())
        layer = nxt
    return layer[0]


def _to_json(o):
    import json as _json
    return _json.dumps(o, ensure_ascii=False, default=str)
