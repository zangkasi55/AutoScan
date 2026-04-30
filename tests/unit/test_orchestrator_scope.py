"""Test orchestrator scope validator (defense in depth, in addition to OPA)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_orch():
    fake_router = type(sys)("packages.mcp_tools.model_router_mcp.router")
    fake_router.complete = lambda **k: None
    parent = type(sys)("packages.mcp_tools.model_router_mcp")
    parent.router = fake_router
    sys.modules.setdefault("packages", type(sys)("packages"))
    sys.modules.setdefault("packages.mcp_tools", type(sys)("packages.mcp_tools"))
    sys.modules["packages.mcp_tools.model_router_mcp"] = parent
    sys.modules["packages.mcp_tools.model_router_mcp.router"] = fake_router

    spec = importlib.util.spec_from_file_location(
        "_orch", ROOT / "apps" / "orchestrator" / "orchestrator.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_orch"] = mod
    spec.loader.exec_module(mod)
    return mod


orch = _load_orch()
_validate_plan_within_scope = orch._validate_plan_within_scope


ROE = {
    "id": "00000000-0000-0000-0000-000000000001",
    "scope": {"cidrs": ["10.0.0.0/24"], "hosts": ["api.example.com"]},
    "exclusions": {"cidrs": ["10.0.0.99/32"], "hosts": ["legacy.example.com"]},
}


def test_in_scope_passes():
    plan = {"phases": [{"steps": [{"target": "10.0.0.5"}]}]}
    _validate_plan_within_scope(plan, ROE)


def test_in_scope_with_port_passes():
    plan = {"phases": [{"steps": [{"target": "10.0.0.5:443"}]}]}
    _validate_plan_within_scope(plan, ROE)


def test_in_scope_hostname_passes():
    plan = {"phases": [{"steps": [{"target": "api.example.com"}]}]}
    _validate_plan_within_scope(plan, ROE)


def test_excluded_cidr_rejected():
    plan = {"phases": [{"steps": [{"target": "10.0.0.99"}]}]}
    with pytest.raises(ValueError, match="excluded"):
        _validate_plan_within_scope(plan, ROE)


def test_out_of_scope_ip_rejected():
    plan = {"phases": [{"steps": [{"target": "8.8.8.8"}]}]}
    with pytest.raises(ValueError, match="out-of-scope"):
        _validate_plan_within_scope(plan, ROE)


def test_excluded_hostname_rejected():
    plan = {"phases": [{"steps": [{"target": "legacy.example.com"}]}]}
    with pytest.raises(ValueError, match="excluded"):
        _validate_plan_within_scope(plan, ROE)


def test_out_of_scope_hostname_rejected():
    plan = {"phases": [{"steps": [{"target": "evil.example.com"}]}]}
    with pytest.raises(ValueError, match="out-of-scope"):
        _validate_plan_within_scope(plan, ROE)
