import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.value_objects import YearMonth


def test_year_month_accepts_year_and_month() -> None:
    value = YearMonth("2024-10")

    assert str(value) == "2024-10"
    assert value.year == 2024
    assert value.month == 10


@pytest.mark.parametrize("value", ["2024-00", "2024-13", "2024-1", "2024-10-01", "10/2024"])
def test_year_month_rejects_other_formats(value: str) -> None:
    with pytest.raises(DomainError):
        YearMonth(value)
