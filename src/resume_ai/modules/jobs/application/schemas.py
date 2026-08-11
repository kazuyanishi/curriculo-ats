from pydantic import BaseModel, ConfigDict, field_validator

from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
    JobPosting,
)


def _require_non_blank(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("must be a string")
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_non_blank_if_present(value: object) -> str | None:
    if value is None:
        return None
    return _require_non_blank(value)


def _reject_importance_for_category(value: object) -> object:
    if isinstance(value, CriterionImportance):
        raise ValueError("criterion importance is not a category")
    return value


def _reject_category_for_importance(value: object) -> object:
    if isinstance(value, CriterionCategory):
        raise ValueError("criterion category is not an importance")
    return value


class _InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JobPostingInput(_InputSchema):
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

    def to_domain(self) -> JobPosting:
        return JobPosting(
            description=self.description,
            title=self.title,
            company=self.company,
            location=self.location,
            source_url=self.source_url,
        )


class JobCriterionInput(_InputSchema):
    category: CriterionCategory
    value: str
    evidence: str
    importance: CriterionImportance = CriterionImportance.UNSPECIFIED

    _validate_category_boundary = field_validator("category", mode="before")(
        _reject_importance_for_category
    )
    _validate_importance_boundary = field_validator("importance", mode="before")(
        _reject_category_for_importance
    )
    _validate_value = field_validator("value")(_require_non_blank)
    _validate_evidence = field_validator("evidence")(_require_non_blank)

    def to_domain(self) -> JobCriterion:
        return JobCriterion(
            category=self.category,
            value=self.value,
            evidence=self.evidence,
            importance=self.importance,
        )


class JobCriteriaInput(_InputSchema):
    criteria: tuple[JobCriterionInput, ...] = ()

    def to_domain(self) -> JobCriteria:
        return JobCriteria(criteria=tuple(item.to_domain() for item in self.criteria))
