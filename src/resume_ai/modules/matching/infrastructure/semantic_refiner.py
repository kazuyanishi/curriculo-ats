import json

from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import (
    build_candidate_evidence_catalog,
)
from resume_ai.modules.matching.application.exceptions import (
    SemanticMatchingGroundingError,
)
from resume_ai.modules.matching.application.semantic_schemas import SemanticMatchBatch
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchStatus,
)
from resume_ai.modules.matching.infrastructure.semantic_matching_prompt import (
    SEMANTIC_MATCHING_SYSTEM_PROMPT,
)


def _criterion_payload(index: int, match: CriterionMatch) -> dict[str, object]:
    criterion = match.criterion
    payload: dict[str, object] = {
        "criterion_index": index,
        "category": criterion.category.value,
        "value": criterion.value,
        "evidence": criterion.evidence,
        "importance": criterion.importance.value,
    }
    if criterion.education_requirement is not None:
        payload["education_requirement"] = {
            "degree_level": criterion.education_requirement.degree_level,
            "field_of_study": criterion.education_requirement.field_of_study,
            "institution": criterion.education_requirement.institution,
            "acceptable_statuses": [
                status.value for status in criterion.education_requirement.acceptable_statuses
            ],
        }
    if criterion.experience_requirement is not None:
        requirement = criterion.experience_requirement
        payload["experience_requirement"] = {
            "role": requirement.role,
            "company": requirement.company,
            "minimum_duration": (
                None
                if requirement.minimum_duration is None
                else {
                    "value": requirement.minimum_duration.value,
                    "unit": requirement.minimum_duration.unit.value,
                }
            ),
        }
    return payload


class AISemanticMatchingRefiner:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def refine(self, candidate: Candidate, result: MatchingResult) -> MatchingResult:
        pending = {
            index: match
            for index, match in enumerate(result.matches)
            if match.status is not MatchStatus.MATCHED
        }
        if not pending:
            return result

        catalog = build_candidate_evidence_catalog(candidate)
        catalog_payload = [{"path": item.path, "text": item.text} for item in catalog]
        user_prompt = json.dumps(
            {
                "criteria": [_criterion_payload(index, match) for index, match in pending.items()],
                "candidate_evidence_catalog": catalog_payload,
            },
            ensure_ascii=False,
        )
        batch = self._client.generate(
            system_prompt=SEMANTIC_MATCHING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SemanticMatchBatch,
        )
        decisions = self._validate_decisions(batch, pending, {item.path for item in catalog})
        decision_by_index = {decision.criterion_index: decision for decision in decisions}
        merged = tuple(
            match
            if index not in decision_by_index
            else CriterionMatch(
                criterion=match.criterion,
                status=decision_by_index[index].status,
                candidate_evidence_paths=(
                    decision_by_index[index].evidence_paths
                    if decision_by_index[index].status is MatchStatus.MATCHED
                    else ()
                ),
            )
            for index, match in enumerate(result.matches)
        )
        return MatchingResult(matches=merged)

    @staticmethod
    def _validate_decisions(batch, pending, catalog_paths):
        decisions = batch.decisions
        indexes = [decision.criterion_index for decision in decisions]
        if set(indexes) != set(pending) or len(indexes) != len(set(indexes)):
            raise SemanticMatchingGroundingError()
        for decision in decisions:
            if any(path not in catalog_paths for path in decision.evidence_paths):
                raise SemanticMatchingGroundingError()
            if decision.status is MatchStatus.MATCHED and not decision.evidence_paths:
                raise SemanticMatchingGroundingError()
        return decisions
