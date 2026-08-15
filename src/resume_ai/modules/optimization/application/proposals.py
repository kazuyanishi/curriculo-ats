from dataclasses import dataclass

from resume_ai.core.exceptions import DomainError


def _require_indexes(values: object) -> None:
    if not isinstance(values, tuple) or not values:
        raise DomainError("target_match_indexes must be a non-empty tuple")
    if any(type(value) is not int or value < 0 for value in values):
        raise DomainError("target_match_indexes must contain only non-negative ints")
    if len(set(values)) != len(values):
        raise DomainError("target_match_indexes must not contain duplicates")


def _require_paths(values: object) -> None:
    if not isinstance(values, tuple) or not values:
        raise DomainError("source_paths must be a non-empty tuple")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise DomainError("source_paths must contain only non-blank strings")
    if len(set(values)) != len(values):
        raise DomainError("source_paths must not contain duplicates")


@dataclass(frozen=True, slots=True)
class OptimizedExperienceStatementProposal:
    text: str
    source_paths: tuple[str, ...]
    target_match_indexes: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise DomainError("text must be a non-blank string")
        _require_paths(self.source_paths)
        _require_indexes(self.target_match_indexes)


@dataclass(frozen=True, slots=True)
class ExperienceOptimizationProposal:
    experience_index: int
    statements: tuple[OptimizedExperienceStatementProposal, ...] = ()

    def __post_init__(self) -> None:
        if type(self.experience_index) is not int or self.experience_index < 0:
            raise DomainError("experience_index must be a non-negative int")
        if not isinstance(self.statements, tuple):
            raise DomainError("statements must be a tuple")
        if not all(
            isinstance(item, OptimizedExperienceStatementProposal) for item in self.statements
        ):
            raise DomainError("statements contains an invalid item")


@dataclass(frozen=True, slots=True)
class CandidateOptimizationProposal:
    experiences: tuple[ExperienceOptimizationProposal, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.experiences, tuple):
            raise DomainError("experiences must be a tuple")
        if not all(isinstance(item, ExperienceOptimizationProposal) for item in self.experiences):
            raise DomainError("experiences contains an invalid item")
