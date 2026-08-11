from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchStatus


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


class ExactCandidateCriterionMatcher:
    def match(
        self,
        candidate: Candidate,
        criterion: JobCriterion,
    ) -> CriterionMatch:
        if criterion.category is CriterionCategory.SKILL:
            items = candidate.skills
        elif criterion.category is CriterionCategory.TECHNOLOGY:
            items = candidate.technologies
        elif criterion.category is CriterionCategory.TOOL:
            items = candidate.tools
        elif criterion.category is CriterionCategory.LANGUAGE:
            items = candidate.languages
        elif criterion.category is CriterionCategory.CERTIFICATION:
            items = candidate.certifications
        else:
            return CriterionMatch(
                criterion=criterion,
                status=MatchStatus.UNSUPPORTED,
            )

        criterion_name = _normalize_name(criterion.value)
        status = (
            MatchStatus.MATCHED
            if any(_normalize_name(item.name) == criterion_name for item in items)
            else MatchStatus.NOT_MATCHED
        )
        return CriterionMatch(criterion=criterion, status=status)
