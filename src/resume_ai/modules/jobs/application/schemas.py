from pydantic import BaseModel, ConfigDict


def _require_non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_non_blank_if_present(value: str | None) -> str | None:
    if value is None:
        return None
    return _require_non_blank(value)


class _InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
