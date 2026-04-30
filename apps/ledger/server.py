"""Append-only evidence ledger HTTP service (FastAPI).

Re-exports the implementation from packages/mcp-tools/evidence-mcp so that
apps/ledger is a deployable wrapper (Helm/Docker) but the source of truth
lives next to the redactor + MCP base.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "mcp-tools"))

# Re-export the FastAPI app
from importlib import import_module
_mod = import_module("evidence-mcp.server")
app = _mod.app
