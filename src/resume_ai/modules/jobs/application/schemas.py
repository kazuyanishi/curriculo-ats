from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    EducationRequirement,
    EducationRequirementStatus,
    EducationRequirementStatusEvidence,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriteria,
    JobCriterion,
    JobPosting,
)


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

    def to_domain(self) -> JobPosting:
        return JobPosting(
            description=self.description,
            title=self.title,
            company=self.company,
            location=self.location,
            source_url=self.source_url,
        )


def _reject_importance_as_category(value: object) -> object:
    if isinstance(value, CriterionImportance):
        raise ValueError("criterion importance is not a category")
    return value


def _reject_category_as_importance(value: object) -> object:
    if isinstance(value, CriterionCategory):
        raise ValueError("criterion category is not an importance")
    return value


class EducationRequirementInput(_InputSchema):
    degree_level: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    acceptable_statuses: tuple[EducationRequirementStatus, ...] = ()
    status_evidence: tuple["EducationRequirementStatusEvidenceInput", ...] = ()

    _validate_degree_level = field_validator("degree_level")(_require_non_blank_if_present)
    _validate_field_of_study = field_validator("field_of_study")(
        _require_non_blank_if_present
    )
    _validate_institution = field_validator("institution")(_require_non_blank_if_present)

    @model_validator(mode="after")
    def _require_at_least_one_requirement(self) -> "EducationRequirementInput":
        if (
            self.degree_level is None
            and self.field_of_study is None
            and self.institution is None
            and not self.acceptable_statuses
        ):
            raise ValueError("education requirement must define at least one requirement")
        return self

    @model_validator(mode="after")
    def _validate_status_evidence_association(self) -> "EducationRequirementInput":
        acceptable_statuses = set(self.acceptable_statuses)
        if any(item.status not in acceptable_statuses for item in self.status_evidence):
            raise ValueError("status evidence must use an acceptable status")
        return self

    def to_domain(self) -> EducationRequirement:
        return EducationRequirement(
            degree_level=self.degree_level,
            field_of_study=self.field_of_study,
            institution=self.institution,
            acceptable_statuses=self.acceptable_statuses,
            status_evidence=tuple(item.to_domain() for item in self.status_evidence),
        )


class EducationRequirementStatusEvidenceInput(_InputSchema):
    status: EducationRequirementStatus
    evidence: str

    _validate_evidence = field_validator("evidence")(_require_non_blank)

    def to_domain(self) -> EducationRequirementStatusEvidence:
        return EducationRequirementStatusEvidence(
            status=self.status,
            evidence=self.evidence,
        )


class ExperienceMinimumDurationInput(_InputSchema):
    value: int
    unit: ExperienceDurationUnit

    @field_validator("value", mode="before")
    @classmethod
    def _validate_positive_value(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("experience duration value must be an int")
        if value <= 0:
            raise ValueError("experience duration value must be greater than zero")
        return value

    def to_domain(self) -> ExperienceMinimumDuration:
        return ExperienceMinimumDuration(value=self.value, unit=self.unit)


class ExperienceRequirementInput(_InputSchema):
    role: str | None = None
    company: str | None = None
    minimum_duration: ExperienceMinimumDurationInput | None = None

    _validate_role = field_validator("role")(_require_non_blank_if_present)
    _validate_company = field_validator("company")(_require_non_blank_if_present)

    @model_validator(mode="after")
    def _require_at_least_one_requirement(self) -> "ExperienceRequirementInput":
        if self.role is None and self.company is None and self.minimum_duration is None:
            raise ValueError("experience requirement must define at least one requirement")
        return self

    def to_domain(self) -> ExperienceRequirement:
        return ExperienceRequirement(
            role=self.role,
            company=self.company,
            minimum_duration=(
                self.minimum_duration.to_domain()
                if self.minimum_duration is not None
                else None
            ),
        )


class JobCriterionInput(_InputSchema):
    category: CriterionCategory
    value: str
    evidence: str
    importance: CriterionImportance = CriterionImportance.UNSPECIFIED
    education_requirement: EducationRequirementInput | None = None
    experience_requirement: ExperienceRequirementInput | None = None

    _validate_category_boundary = field_validator("category", mode="before")(
        _reject_importance_as_category
    )
    _validate_importance_boundary = field_validator("importance", mode="before")(
        _reject_category_as_importance
    )
    _validate_value = field_validator("value")(_require_non_blank)
    _validate_evidence = field_validator("evidence")(_require_non_blank)

    @model_validator(mode="after")
    def _validate_education_requirement_category(self) -> "JobCriterionInput":
        if (
            self.education_requirement is not None
            and self.category is not CriterionCategory.EDUCATION
        ):
            raise ValueError("education_requirement requires education criterion category")
        return self

    @model_validator(mode="after")
    def _validate_experience_requirement_category(self) -> "JobCriterionInput":
        if (
            self.experience_requirement is not None
            and self.category is not CriterionCategory.EXPERIENCE
        ):
            raise ValueError(
                "experience_requirement requires experience criterion category"
            )
        return self

    def to_domain(self) -> JobCriterion:
        return JobCriterion(
            category=self.category,
            value=self.value,
            evidence=self.evidence,
            importance=self.importance,
            education_requirement=(
                self.education_requirement.to_domain()
                if self.education_requirement is not None
                else None
            ),
            experience_requirement=(
                self.experience_requirement.to_domain()
                if self.experience_requirement is not None
                else None
            ),
        )


class JobCriteriaInput(_InputSchema):
    criteria: tuple[JobCriterionInput, ...] = ()

    def to_domain(self) -> JobCriteria:
        return JobCriteria(criteria=tuple(item.to_domain() for item in self.criteria))
