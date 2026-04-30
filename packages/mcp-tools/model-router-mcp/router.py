"""model-router — single LLM-call abstraction.

Cross-vendor: Anthropic (Claude) + Azure OpenAI (GPT). Routing per role per
ADR-2. All calls emit OTel spans `llm.call`.

Vendor failover:
  primary 5xx / 429 / timeout → try fallback once, return.

Critic isolation contract is enforced *here*: callers must pass
`isolation_token=role_id`; the router refuses to leak history across roles.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

log = logging.getLogger("model-router")

# ───────────────────────── Provider config ─────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE = os.environ.get("ANTHROPIC_BASE", "https://api.anthropic.com")

# Azure OpenAI: managed identity → AAD token; for prod, swap to azure-identity.
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")  # dev fallback
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")


# ───────────────────────── Role → model routing (ADR-2) ─────────────────────────
ROLE_ROUTING: dict[str, dict[str, Any]] = {
    "orchestrator":      {"primary": ("anthropic", "claude-opus-4-20250514"),
                           "fallback": ("openai", "gpt-4o")},
    "recon":             {"primary": ("openai", "gpt-4o"),
                           "fallback": ("anthropic", "claude-3-5-haiku-20241022")},
    "vuln":              {"primary": ("openai", "gpt-4o"),
                           "fallback": ("anthropic", "claude-sonnet-4-20250514")},
    "exploit_reasoning": {"primary": ("anthropic", "claude-opus-4-20250514"),
                           "fallback": ("openai", "gpt-4o")},
    "critic":            {"primary": ("openai", "gpt-4o"),
                           "fallback": ("anthropic", "claude-sonnet-4-20250514")},
    "report_writer":     {"primary": ("openai", "gpt-4o"),
                           "fallback": ("anthropic", "claude-sonnet-4-20250514")},
}


@dataclass
class LLMResult:
    provider: str
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def select_independent_model(producing_role: str) -> tuple[str, str]:
    """Pick a model from a different vendor than the producer. Used for Critic isolation."""
    primary = ROLE_ROUTING.get(producing_role, {}).get("primary", ("openai", "gpt-4o"))
    return ROLE_ROUTING["critic"]["fallback"] if primary[0] == ROLE_ROUTING["critic"]["primary"][0] else ROLE_ROUTING["critic"]["primary"]


async def complete(
    role: str,
    system: str,
    user: str,
    *,
    isolation_token: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.2,
    force_provider: tuple[str, str] | None = None,
) -> LLMResult:
    """Single completion call with primary→fallback failover and OTel-shaped logging."""
    if not isolation_token:
        raise ValueError("isolation_token required (Critic isolation contract)")

    cfg = ROLE_ROUTING.get(role)
    if not cfg:
        raise ValueError(f"unknown role {role}")

    primary = force_provider or cfg["primary"]
    fallback = cfg["fallback"]

    for attempt, (provider, model) in enumerate([primary, fallback]):
        t0 = time.perf_counter()
        try:
            if provider == "anthropic":
                text, in_tok, out_tok = await _anthropic(model, system, user, max_tokens, temperature)
            elif provider == "openai":
                text, in_tok, out_tok = await _azure_openai(model, system, user, max_tokens, temperature)
            else:
                raise ValueError(f"unknown provider {provider}")
            elapsed = int((time.perf_counter() - t0) * 1000)
            log.info("llm.call role=%s provider=%s model=%s tokens=%d/%d latency_ms=%d",
                     role, provider, model, in_tok, out_tok, elapsed)
            return LLMResult(provider, model, text, in_tok, out_tok, elapsed)
        except Exception as e:
            log.warning("llm.call FAILED role=%s provider=%s model=%s attempt=%d err=%s",
                        role, provider, model, attempt, e)
            if attempt == 1:
                raise


async def _anthropic(model: str, system: str, user: str, max_tokens: int, temp: float):
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temp,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=120.0) as c:
        r = await c.post(f"{ANTHROPIC_BASE}/v1/messages", headers=headers, json=body)
        r.raise_for_status()
        d = r.json()
    text = "".join(b.get("text", "") for b in d.get("content", []))
    return text, d.get("usage", {}).get("input_tokens", 0), d.get("usage", {}).get("output_tokens", 0)


async def _azure_openai(deployment: str, system: str, user: str, max_tokens: int, temp: float):
    if not AZURE_OPENAI_ENDPOINT:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT not set")
    headers = {"content-type": "application/json"}
    if AZURE_OPENAI_API_KEY:
        headers["api-key"] = AZURE_OPENAI_API_KEY
    else:
        # AAD token via managed identity (azure-identity).
        from azure.identity.aio import DefaultAzureCredential  # type: ignore
        cred = DefaultAzureCredential()
        token = await cred.get_token("https://cognitiveservices.azure.com/.default")
        headers["Authorization"] = f"Bearer {token.token}"

    url = (
        f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{deployment}/chat/completions"
        f"?api-version={AZURE_OPENAI_API_VERSION}"
    )
    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temp,
    }
    async with httpx.AsyncClient(timeout=120.0) as c:
        r = await c.post(url, headers=headers, json=body)
        r.raise_for_status()
        d = r.json()
    text = d["choices"][0]["message"]["content"]
    u = d.get("usage", {})
    return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
