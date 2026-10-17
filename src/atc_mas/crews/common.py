"""Helpers shared by the crew factories."""

from __future__ import annotations

from typing import Any

from atc_mas.config import get_llm_model


def agent_llm_kwargs(llm: Any | None = None) -> dict[str, Any]:
    """Return ``{"llm": ...}`` if an LLM is given or configured, else ``{}``.

    With ``{}`` CrewAI falls back to its own environment-based default. No
    provider or model name is hard-coded here.
    """
    chosen = llm if llm is not None else get_llm_model()
    return {"llm": chosen} if chosen is not None else {}
