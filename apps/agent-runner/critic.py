"""Critic agent — strict isolation per build-spec §3.2.

Implementation details that are CONTRACT (do not weaken):
  • Build a fresh context. NEVER include orchestrator_history.
  • Use a different vendor than the producing agent.
  • Receive only signed evidence attestations + finding title.
  • Produce a structured CriticVerdict.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.mcp_tools.model_router_mcp import router  # type: ignore  # noqa: E402

log = logging.getLogger("critic")

FORBIDDEN_INPUT_KEYS = {
    "orchestrator_history",
    "producing_agent_messages",
    "agent_chain_of_thought",
    "raw_prompt_history",
}

CRITIC_SYSTEM = """You are the Critic. You receive ONLY signed evidence
attestations and the finding's headline claim. You do NOT receive the
orchestrator's history, the producing agent's prompt, or any other agent's
reasoning.

Given the signed evidence, can you INDEPENDENTLY re-derive the same
conclusion? Be skeptical. If evidence is weak, vague, or could be explained
by a benign cause, mark NOT confirmed.

Respond ONLY with JSON:
{"confirmed": bool, "reasons": ["...", "..."]}"""


@dataclass
class CriticContext:
    target_hypothesis: str
    scene_facts: list[dict[str, Any]]


@dataclass
class CriticVerdict:
    confirmed: bool
    model_used: str
    reasons: list[str]


def build_critic_context(
    finding: dict[str, Any],
    signed_evidence: list[dict[str, Any]],
    forbidden_inputs: set[str] | None = None,
) -> CriticContext:
    forbidden = (forbidden_inputs or set()) | FORBIDDEN_INPUT_KEYS
    leaked = forbidden & set(finding.keys())
    if leaked:
        raise RuntimeError(f"Critic isolation violated; leaked inputs: {leaked}")
    return CriticContext(
        target_hypothesis=finding["titleEn"],
        scene_facts=signed_evidence,
    )


async def run_critic(
    finding: dict[str, Any],
    signed_evidence: list[dict[str, Any]],
) -> CriticVerdict:
    ctx = build_critic_context(finding, signed_evidence)
    producing_role = (finding.get("producedBy") or {}).get("agent", "vuln")
    independent_provider, independent_model = router.select_independent_model(producing_role)

    user = (
        f"FINDING TITLE: {ctx.target_hypothesis}\n\n"
        f"SIGNED EVIDENCE ATTESTATIONS (n={len(ctx.scene_facts)}):\n"
        f"{json.dumps(ctx.scene_facts, ensure_ascii=False, indent=2)}\n\n"
        "Re-derive the conclusion or refute it."
    )
    res = await router.complete(
        role="critic",
        system=CRITIC_SYSTEM,
        user=user,
        isolation_token=f"critic:{finding.get('id')}",
        force_provider=(independent_provider, independent_model),
        temperature=0.1,
        max_tokens=1500,
    )
    parsed = _parse_json(res.text)
    return CriticVerdict(
        confirmed=bool(parsed.get("confirmed", False)),
        model_used=f"{res.provider}:{res.model}",
        reasons=list(parsed.get("reasons", [])),
    )


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text)
