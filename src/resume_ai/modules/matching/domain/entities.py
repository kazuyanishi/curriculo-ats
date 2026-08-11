from dataclasses import dataclass
from enum import StrEnum

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobCriterion


class MatchStatus(StrEnum):
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"


@dataclass(frozen=True, slots=True)
class CriterionMatch:
    criterion: JobCriterion
    status: MatchStatus

    def __post_init__(self) -> None:
        if not isinstance(self.criterion, JobCriterion):
            raise DomainError("criterion must be a JobCriterion")
        if not isinstance(self.status, MatchStatus):
            raise DomainError("status must be a MatchStatus")


@dataclass(frozen=True, slots=True)
class MatchingResult:
    matches: tuple[CriterionMatch, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.matches, tuple):
            raise DomainError("matches must be a tuple of CriterionMatch")
        if not all(isinstance(match, CriterionMatch) for match in self.matches):
            raise DomainError("matches must contain only CriterionMatch")

    @property
    def matched(self) -> tuple[CriterionMatch, ...]:
        return tuple(match for match in self.matches if match.status is MatchStatus.MATCHED)

    @property
    def not_matched(self) -> tuple[CriterionMatch, ...]:
        return tuple(
            match for match in self.matches if match.status is MatchStatus.NOT_MATCHED
        )

    @property
    def total(self) -> int:
        return len(self.matches)

    @property
    def matched_count(self) -> int:
        return len(self.matched)

    @property
    def not_matched_count(self) -> int:
        return len(self.not_matched)
