from collections.abc import Mapping
from dataclasses import dataclass, field
import os


@dataclass(frozen=True, slots=True)
class AIConfig:
    api_key: str = field(repr=False)
    model: str


def _require_non_blank(name: str, value: str | None) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def load_ai_config(
    environ: Mapping[str, str] | None = None,
) -> AIConfig:
    source = os.environ if environ is None else environ
    api_key = _require_non_blank(
        "RESUME_AI_API_KEY", source.get("RESUME_AI_API_KEY")
    )
    model = _require_non_blank("RESUME_AI_MODEL", source.get("RESUME_AI_MODEL"))
    return AIConfig(api_key=api_key, model=model)
