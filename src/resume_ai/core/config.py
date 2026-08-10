import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

_DEFAULT_ENVIRONMENT = "development"
_SUPPORTED_ENVIRONMENTS = frozenset({"development", "test", "production"})


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable application configuration."""

    project_root: Path
    package_root: Path
    data_dir: Path
    output_dir: Path
    environment: str


def _normalize_environment(value: str | None) -> str:
    environment = (value or "").strip().lower()
    if not environment:
        return _DEFAULT_ENVIRONMENT
    if environment not in _SUPPORTED_ENVIRONMENTS:
        supported = ", ".join(sorted(_SUPPORTED_ENVIRONMENTS))
        raise ValueError(f"Invalid RESUME_AI_ENV {value!r}; expected one of: {supported}")
    return environment


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    """Build application configuration from paths and the optional environment mapping."""
    environment_source = os.environ if environ is None else environ
    return AppConfig(
        project_root=PROJECT_ROOT,
        package_root=PACKAGE_ROOT,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        environment=_normalize_environment(environment_source.get("RESUME_AI_ENV")),
    )
