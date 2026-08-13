from dataclasses import dataclass

from resume_ai.core.exceptions import DomainError


@dataclass(frozen=True, slots=True, order=True)
class YearMonth:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or len(self.value) != 7 or self.value[4] != "-":
            raise DomainError("YearMonth must use YYYY-MM format")
        try:
            year = int(self.value[:4])
            month = int(self.value[5:])
        except ValueError as error:
            raise DomainError("YearMonth must use YYYY-MM format") from error
        if year < 1 or not 1 <= month <= 12:
            raise DomainError("YearMonth must use YYYY-MM format")

    def __str__(self) -> str:
        return self.value

    @property
    def year(self) -> int:
        return int(self.value[:4])

    @property
    def month(self) -> int:
        return int(self.value[5:])
