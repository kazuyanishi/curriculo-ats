from pydantic import BaseModel, ConfigDict, field_validator


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


class JobPostingInput(_InputSchema):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    description: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    source_url: str | None = None

    _validate_description = field_validator("description")(_require_non_blank)
    _validate_title = field_validator("title")(_require_non_blank_if_present)
    _validate_company = field_validator("company")(_require_non_blank_if_present)
    _validate_location = field_validator("location")(_require_non_blank_if_present)
    _validate_source_url = field_validator("source_url")(_require_non_blank_if_present)
