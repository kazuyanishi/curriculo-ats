from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobCriteria, JobCriterion, JobPosting


class EducationRequirementTruthGate:
    def validate(self, criterion: JobCriterion) -> None:
        requirement = criterion.education_requirement
        if requirement is None:
            return None

        if (
            requirement.degree_level is not None
            and requirement.degree_level not in criterion.evidence
        ):
            raise DomainError(
                "education degree_level is not present in criterion evidence"
            )
        if (
            requirement.field_of_study is not None
            and requirement.field_of_study not in criterion.evidence
        ):
            raise DomainError(
                "education field_of_study is not present in criterion evidence"
            )
        if (
            requirement.institution is not None
            and requirement.institution not in criterion.evidence
        ):
            raise DomainError(
                "education institution is not present in criterion evidence"
            )

        for item in requirement.status_evidence:
            if item.evidence not in criterion.evidence:
                raise DomainError(
                    "education status evidence is not present in criterion evidence"
                )

        grounded_statuses = {item.status for item in requirement.status_evidence}
        if any(status not in grounded_statuses for status in requirement.acceptable_statuses):
            raise DomainError("education acceptable status requires status evidence")


class ExperienceRequirementTruthGate:
    def validate(self, criterion: JobCriterion) -> None:
        requirement = criterion.experience_requirement
        if requirement is None:
            return None

        if requirement.role is not None and requirement.role not in criterion.evidence:
            raise DomainError(
                "experience role is not present in criterion evidence"
            )
        if (
            requirement.company is not None
            and requirement.company not in criterion.evidence
        ):
            raise DomainError(
                "experience company is not present in criterion evidence"
            )
        if requirement.minimum_duration is not None:
            if requirement.minimum_duration_evidence is None:
                raise DomainError(
                    "experience minimum duration requires duration evidence"
                )
            if requirement.minimum_duration_evidence not in criterion.evidence:
                raise DomainError(
                    "experience duration evidence is not present in criterion evidence"
                )


class JobCriteriaTruthGate:
    def validate(self, job: JobPosting, criteria: JobCriteria) -> None:
        for criterion in criteria.criteria:
            if criterion.evidence not in job.description:
                raise DomainError(
                    "Job criterion evidence is not present in the job description"
                )
            EducationRequirementTruthGate().validate(criterion)
            ExperienceRequirementTruthGate().validate(criterion)
