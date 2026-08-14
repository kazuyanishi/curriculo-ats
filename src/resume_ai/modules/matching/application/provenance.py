from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.catalog import build_candidate_evidence_catalog
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus


class MatchingProvenanceError(Exception):
    """Raised when matching provenance cannot be validated safely."""


class MatchingProvenanceGate:
    def validate(self, candidate: Candidate, result: MatchingResult) -> None:
        paths = {item.path for item in build_candidate_evidence_catalog(candidate)}
        for index, match in enumerate(result.matches):
            if match.status is MatchStatus.MATCHED and not match.candidate_evidence_paths:
                raise MatchingProvenanceError(f"invalid provenance for criterion_index={index}")
            if match.status is not MatchStatus.MATCHED and match.candidate_evidence_paths:
                raise MatchingProvenanceError(f"invalid provenance for criterion_index={index}")
            if any(path not in paths for path in match.candidate_evidence_paths):
                raise MatchingProvenanceError(f"invalid provenance for criterion_index={index}")
