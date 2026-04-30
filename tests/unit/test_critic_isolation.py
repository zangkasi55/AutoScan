"""Critic isolation contract test — build-spec §3.2."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_critic():
    # Stub out the model-router import (hyphen path; not loadable as module).
    fake_router = type(sys)("packages.mcp_tools.model_router_mcp.router")
    fake_router.complete = lambda **k: None
    fake_router.select_independent_model = lambda role: ("anthropic", "claude")
    parent = type(sys)("packages.mcp_tools.model_router_mcp")
    parent.router = fake_router
    sys.modules.setdefault("packages", type(sys)("packages"))
    sys.modules.setdefault("packages.mcp_tools", type(sys)("packages.mcp_tools"))
    sys.modules["packages.mcp_tools.model_router_mcp"] = parent
    sys.modules["packages.mcp_tools.model_router_mcp.router"] = fake_router

    spec = importlib.util.spec_from_file_location(
        "_critic", ROOT / "apps" / "agent-runner" / "critic.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_critic"] = mod
    spec.loader.exec_module(mod)
    return mod


critic = _load_critic()


def _finding(**overrides):
    base = {
        "id": "00000000-0000-0000-0000-000000000001",
        "titleEn": "SSRF on /api/preview",
        "titleTh": "SSRF บนเส้นทาง /api/preview",
        "producedBy": {"agent": "vuln", "model": "gpt-4o", "provider": "openai"},
    }
    base.update(overrides)
    return base


SIGNED_EVIDENCE = [{"idx": 1, "leaf_hash": "ab"*32, "payload_hash": "cd"*32}]


def test_clean_finding_builds():
    ctx = critic.build_critic_context(_finding(), SIGNED_EVIDENCE)
    assert ctx.target_hypothesis.startswith("SSRF")
    assert ctx.scene_facts == SIGNED_EVIDENCE


@pytest.mark.parametrize("forbidden_key", sorted(critic.FORBIDDEN_INPUT_KEYS))
def test_forbidden_key_rejects(forbidden_key):
    finding = _finding(**{forbidden_key: "leaked!"})
    with pytest.raises(RuntimeError, match="isolation violated"):
        critic.build_critic_context(finding, SIGNED_EVIDENCE)


def test_extra_forbidden_via_argument():
    finding = _finding(custom_leak="bad")
    with pytest.raises(RuntimeError, match="isolation violated"):
        critic.build_critic_context(finding, SIGNED_EVIDENCE, forbidden_inputs={"custom_leak"})
