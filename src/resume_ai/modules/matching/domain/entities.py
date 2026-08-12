from dataclasses import dataclass
from enum import StrEnum

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobCriterion


class MatchStatus(StrEnum):
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"
    UNSUPPORTED = "unsupported"


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
    def unsupported(self) -> tuple[CriterionMatch, ...]:
        return tuple(match for match in self.matches if match.status is MatchStatus.UNSUPPORTED)

    @property
    def total(self) -> int:
        return len(self.matches)

    @property
    def matched_count(self) -> int:
        return len(self.matched)

    @property
    def not_matched_count(self) -> int:
        return len(self.not_matched)

    @property
    def unsupported_count(self) -> int:
        return len(self.unsupported)


@dataclass(frozen=True, slots=True)
class GapAnalysisResult:
    gaps: tuple[CriterionMatch, ...] = ()
    unsupported: tuple[CriterionMatch, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.gaps, tuple):
            raise DomainError("gaps must be a tuple of CriterionMatch")
        if not isinstance(self.unsupported, tuple):
            raise DomainError("unsupported must be a tuple of CriterionMatch")
        if not all(isinstance(match, CriterionMatch) for match in self.gaps):
            raise DomainError("gaps must contain only CriterionMatch")
        if not all(isinstance(match, CriterionMatch) for match in self.unsupported):
            raise DomainError("unsupported must contain only CriterionMatch")


@dataclass(frozen=True, slots=True)
class MatchingScore:
    score: float | None
    coverage: float | None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("score", self.score),
            ("coverage", self.coverage),
        ):
            if value is None:
                continue
            if type(value) is not float:
                raise DomainError(f"{field_name} must be a float or None")
            if not 0.0 <= value <= 1.0:
                raise DomainError(f"{field_name} must be between 0.0 and 1.0")
