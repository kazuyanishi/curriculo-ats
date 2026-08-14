import re
from dataclasses import dataclass

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.domain.entities import MatchingResult, MatchStatus

_EXPERIENCE_PATH = re.compile(r"^experiences\[(\d+)]\.")


def _require_index(name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise DomainError(f"{name} must be a non-negative int")


def _require_indexes(name: str, values: object) -> None:
    if not isinstance(values, tuple) or not values:
        raise DomainError(f"{name} must be a non-empty tuple")
    if any(type(value) is not int or value < 0 for value in values):
        raise DomainError(f"{name} must contain only non-negative ints")
    if len(set(values)) != len(values):
        raise DomainError(f"{name} must not contain duplicates")


def _require_paths(values: object) -> None:
    if not isinstance(values, tuple) or not values:
        raise DomainError("evidence_paths must be a non-empty tuple")
    if any(not isinstance(path, str) or not path.strip() for path in values):
        raise DomainError("evidence_paths must contain only non-blank strings")
    if len(set(values)) != len(values):
        raise DomainError("evidence_paths must not contain duplicates")


@dataclass(frozen=True, slots=True)
class ExperienceOptimizationContext:
    experience_index: int
    match_indexes: tuple[int, ...]
    evidence_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_index("experience_index", self.experience_index)
        _require_indexes("match_indexes", self.match_indexes)
        _require_paths(self.evidence_paths)


@dataclass(frozen=True, slots=True)
class StandaloneOptimizationContext:
    match_index: int
    evidence_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_index("match_index", self.match_index)
        _require_paths(self.evidence_paths)


@dataclass(frozen=True, slots=True)
class CandidateOptimizationPlan:
    experience_contexts: tuple[ExperienceOptimizationContext, ...] = ()
    standalone_contexts: tuple[StandaloneOptimizationContext, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.experience_contexts, tuple):
            raise DomainError("experience_contexts must be a tuple")
        if not all(
            isinstance(item, ExperienceOptimizationContext) for item in self.experience_contexts
        ):
            raise DomainError("experience_contexts contains an invalid item")
        if not isinstance(self.standalone_contexts, tuple):
            raise DomainError("standalone_contexts must be a tuple")
        if not all(
            isinstance(item, StandaloneOptimizationContext) for item in self.standalone_contexts
        ):
            raise DomainError("standalone_contexts contains an invalid item")


def _experience_index(paths: tuple[str, ...]) -> int | None:
    indexes = []
    for path in paths:
        match = _EXPERIENCE_PATH.match(path)
        if match is None:
            return None
        indexes.append(int(match.group(1)))
    if len(set(indexes)) != 1:
        return None
    return indexes[0]


class BuildCandidateOptimizationPlan:
    def __init__(self, provenance_gate: MatchingProvenanceGate) -> None:
        self._provenance_gate = provenance_gate

    def execute(
        self,
        candidate: Candidate,
        matching: MatchingResult,
    ) -> CandidateOptimizationPlan:
        self._provenance_gate.validate(candidate, matching)
        grouped: dict[int, tuple[list[int], list[str]]] = {}
        standalone: list[StandaloneOptimizationContext] = []

        for match_index, match in enumerate(matching.matches):
            if match.status is not MatchStatus.MATCHED:
                continue
            experience_index = _experience_index(match.candidate_evidence_paths)
            if experience_index is None:
                standalone.append(
                    StandaloneOptimizationContext(match_index, match.candidate_evidence_paths)
                )
                continue
            match_indexes, paths = grouped.setdefault(experience_index, ([], []))
            match_indexes.append(match_index)
            for path in match.candidate_evidence_paths:
                if path not in paths:
                    paths.append(path)

        return CandidateOptimizationPlan(
            experience_contexts=tuple(
                ExperienceOptimizationContext(index, tuple(indexes), tuple(paths))
                for index, (indexes, paths) in grouped.items()
            ),
            standalone_contexts=tuple(standalone),
        )
