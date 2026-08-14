from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    GapAnalysisResult,
    MatchingResult,
    MatchingScore,
    MatchStatus,
)


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


def complete_calendar_months(start_date: YearMonth, end_date: YearMonth) -> int:
    months = (end_date.year - start_date.year) * 12
    months += end_date.month - start_date.month

    return months


class ExactCandidateCriterionMatcher:
    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        if criterion.category is CriterionCategory.EDUCATION:
            return EducationCandidateCriterionMatcher().match(candidate, criterion)
        if criterion.category is CriterionCategory.EXPERIENCE:
            return ExperienceCandidateCriterionMatcher().match(candidate, criterion)
        if criterion.category is CriterionCategory.SKILL:
            items = candidate.skills
            collection = "skills"
        elif criterion.category is CriterionCategory.TECHNOLOGY:
            items = candidate.technologies
            collection = "technologies"
        elif criterion.category is CriterionCategory.TOOL:
            items = candidate.tools
            collection = "tools"
        elif criterion.category is CriterionCategory.LANGUAGE:
            items = candidate.languages
            collection = "languages"
        elif criterion.category is CriterionCategory.CERTIFICATION:
            items = candidate.certifications
            collection = "certifications"
        else:
            return CriterionMatch(
                criterion=criterion,
                status=MatchStatus.UNSUPPORTED,
            )

        criterion_name = _normalize_name(criterion.value)
        index = next(
            (
                index
                for index, item in enumerate(items)
                if _normalize_name(item.name) == criterion_name
            ),
            None,
        )
        if index is None:
            return CriterionMatch(criterion=criterion, status=MatchStatus.NOT_MATCHED)
        return CriterionMatch(
            criterion=criterion,
            status=MatchStatus.MATCHED,
            candidate_evidence_paths=(f"{collection}[{index}].name",),
        )


class ExperienceCandidateCriterionMatcher:
    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        requirement = criterion.experience_requirement
        if criterion.category is not CriterionCategory.EXPERIENCE or requirement is None:
            return CriterionMatch(criterion=criterion, status=MatchStatus.UNSUPPORTED)

        relevant_experiences = []
        for index, experience in enumerate(candidate.experiences):
            role_matches = requirement.role is None or _normalize_name(
                experience.role
            ) == _normalize_name(requirement.role)
            company_matches = requirement.company is None or _normalize_name(
                experience.company
            ) == _normalize_name(requirement.company)
            if role_matches and company_matches:
                relevant_experiences.append((index, experience))

        if requirement.minimum_duration is None:
            if not relevant_experiences:
                return CriterionMatch(criterion=criterion, status=MatchStatus.NOT_MATCHED)
            index, _ = relevant_experiences[0]
            return CriterionMatch(
                criterion=criterion,
                status=MatchStatus.MATCHED,
                candidate_evidence_paths=self._paths(requirement, index, include_duration=False),
            )

        if not relevant_experiences or len(relevant_experiences) > 1:
            status = (
                MatchStatus.NOT_MATCHED if not relevant_experiences else MatchStatus.UNSUPPORTED
            )
            return CriterionMatch(criterion=criterion, status=status)

        index, experience = relevant_experiences[0]
        if experience.end_date is None:
            return CriterionMatch(criterion=criterion, status=MatchStatus.UNSUPPORTED)

        required_months = (
            requirement.minimum_duration.value
            if requirement.minimum_duration.unit.value == "months"
            else requirement.minimum_duration.value * 12
        )
        actual_months = complete_calendar_months(experience.start_date, experience.end_date)
        if actual_months < required_months:
            return CriterionMatch(criterion=criterion, status=MatchStatus.NOT_MATCHED)
        return CriterionMatch(
            criterion=criterion,
            status=MatchStatus.MATCHED,
            candidate_evidence_paths=self._paths(requirement, index, include_duration=True),
        )

    @staticmethod
    def _paths(requirement, index: int, *, include_duration: bool) -> tuple[str, ...]:
        paths = []
        if requirement.role is not None:
            paths.append(f"experiences[{index}].role")
        if requirement.company is not None:
            paths.append(f"experiences[{index}].company")
        if include_duration:
            paths.extend((f"experiences[{index}].start_date", f"experiences[{index}].end_date"))
        return tuple(paths)


class EducationCandidateCriterionMatcher:
    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        requirement = criterion.education_requirement
        if (
            criterion.category is not CriterionCategory.EDUCATION
            or requirement is None
            or requirement.degree_level is not None
            or (requirement.field_of_study is None and requirement.institution is None)
        ):
            return CriterionMatch(criterion=criterion, status=MatchStatus.UNSUPPORTED)

        acceptable_statuses = {status.value for status in requirement.acceptable_statuses}
        for index, education in enumerate(candidate.education):
            field_matches = requirement.field_of_study is None or _normalize_name(
                education.course
            ) == _normalize_name(requirement.field_of_study)
            institution_matches = requirement.institution is None or _normalize_name(
                education.institution
            ) == _normalize_name(requirement.institution)
            status_matches = (
                not acceptable_statuses or education.status.value in acceptable_statuses
            )
            if field_matches and institution_matches and status_matches:
                paths = []
                if requirement.field_of_study is not None:
                    paths.append(f"education[{index}].course")
                if requirement.institution is not None:
                    paths.append(f"education[{index}].institution")
                if acceptable_statuses:
                    paths.append(f"education[{index}].status")
                return CriterionMatch(
                    criterion=criterion,
                    status=MatchStatus.MATCHED,
                    candidate_evidence_paths=tuple(paths),
                )

        return CriterionMatch(criterion=criterion, status=MatchStatus.NOT_MATCHED)


class MatchingScoreCalculator:
    def calculate(self, result: MatchingResult) -> MatchingScore:
        evaluated_count = result.matched_count + result.not_matched_count
        score = None if evaluated_count == 0 else result.matched_count / evaluated_count
        coverage = None if result.total == 0 else evaluated_count / result.total
        return MatchingScore(score=score, coverage=coverage)


class DeterministicGapAnalyzer:
    def analyze(self, result: MatchingResult) -> GapAnalysisResult:
        gaps = tuple(match for match in result.matches if match.status is MatchStatus.NOT_MATCHED)
        unsupported = tuple(
            match for match in result.matches if match.status is MatchStatus.UNSUPPORTED
        )
        return GapAnalysisResult(gaps=gaps, unsupported=unsupported)
