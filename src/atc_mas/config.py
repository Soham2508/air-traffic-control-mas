"""Central configuration for the ATC MAS.

This module is the **single source of truth** for separation minima and other
runtime settings. Do not duplicate threshold constants in other modules; import
``DEFAULT_SEPARATION_MINIMA`` (or accept a ``SeparationMinima`` argument)
instead.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field


class SeparationMinima(BaseModel):
    """Separation thresholds used for conflict detection.

    A conflict is reported when, at the evaluated closest-approach time, the
    horizontal distance is ``<= lateral_threshold_nm`` **and** the vertical
    distance is ``<= vertical_threshold_ft`` (behaviour inherited from the
    reference notebook).

    Field names intentionally mirror the keyword arguments of the reference
    notebook's ``detect_conflicts`` function.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    lateral_threshold_nm: float = Field(
        default=5.0, gt=0, allow_inf_nan=False, description="Horizontal separation minimum (NM)."
    )
    vertical_threshold_ft: float = Field(
        default=1000.0, gt=0, allow_inf_nan=False, description="Vertical separation minimum (ft)."
    )


#: Default minima from ``notebooks/reference/ConflictDetection.ipynb``.
DEFAULT_SEPARATION_MINIMA = SeparationMinima()

#: Environment variable that selects the LLM used by CrewAI agents.
#: When unset, CrewAI's own default/environment configuration is used.
#: No provider names or credentials are hard-coded in source.
LLM_MODEL_ENV_VAR = "ATC_MAS_LLM_MODEL"


def get_llm_model() -> str | None:
    """Return the configured LLM model identifier, or ``None`` if unset."""
    value = os.environ.get(LLM_MODEL_ENV_VAR, "").strip()
    return value or None
