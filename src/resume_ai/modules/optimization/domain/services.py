from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.jobs.domain.entities import CriterionCategory
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


class DeterministicCandidateOptimizer:
    def optimize(self, candidate: Candidate, result: MatchingResult) -> Candidate:
        matched_names = {
            category: {
                _normalize_name(match.criterion.value)
                for match in result.matches
                if match.status is MatchStatus.MATCHED
                and match.criterion.category is category
            }
            for category in (
                CriterionCategory.SKILL,
                CriterionCategory.TECHNOLOGY,
                CriterionCategory.TOOL,
                CriterionCategory.LANGUAGE,
                CriterionCategory.CERTIFICATION,
            )
        }

        return Candidate(
            personal_info=candidate.personal_info,
            contact_info=candidate.contact_info,
            professional_links=candidate.professional_links,
            experiences=candidate.experiences,
            education=candidate.education,
            skills=self._prioritize(candidate.skills, matched_names[CriterionCategory.SKILL]),
            technologies=self._prioritize(
                candidate.technologies, matched_names[CriterionCategory.TECHNOLOGY]
            ),
            tools=self._prioritize(candidate.tools, matched_names[CriterionCategory.TOOL]),
            languages=self._prioritize(
                candidate.languages, matched_names[CriterionCategory.LANGUAGE]
            ),
            certifications=self._prioritize(
                candidate.certifications, matched_names[CriterionCategory.CERTIFICATION]
            ),
            projects=candidate.projects,
        )

    @staticmethod
    def _prioritize(items: tuple[object, ...], matched_names: set[str]) -> tuple[object, ...]:
        matched = tuple(
            item for item in items if _normalize_name(item.name) in matched_names
        )
        not_matched = tuple(
            item for item in items if _normalize_name(item.name) not in matched_names
        )
        return matched + not_matched
