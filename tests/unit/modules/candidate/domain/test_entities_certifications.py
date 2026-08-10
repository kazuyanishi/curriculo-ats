from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import Certification


def test_certification_accepts_minimum_data() -> None:
    certification = Certification("Example Cloud Certification", "Example Cloud")

    assert certification.issue_date is None
    assert certification.expiration_date is None
    assert certification.credential_id is None
    assert certification.credential_url is None


def test_certification_accepts_complete_data_and_preserves_values() -> None:
    issue_date = date(2025, 1, 1)
    expiration_date = date(2028, 1, 1)
    credential_id = "ABC-XyZ-123"
    credential_url = "https://Example.com/Credential/ABC-123"
    certification = Certification(
        "Example Professional Certification",
        "Example Institute",
        issue_date,
        expiration_date,
        credential_id,
        credential_url,
    )

    assert certification.name == "Example Professional Certification"
    assert certification.issuer == "Example Institute"
    assert certification.issue_date == issue_date
    assert certification.expiration_date == expiration_date
    assert certification.credential_id == credential_id
    assert certification.credential_url == credential_url


@pytest.mark.parametrize("field", ["name", "issuer"])
@pytest.mark.parametrize("value", ["", "   "])
def test_certification_rejects_empty_required_text(field: str, value: str) -> None:
    values = {"name": "Example Certification", "issuer": "Example Institute"}
    values[field] = value

    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        Certification(**values)


@pytest.mark.parametrize("field", ["issue_date", "expiration_date"])
def test_certification_rejects_string_dates(field: str) -> None:
    values = {"name": "Example Certification", "issuer": "Example Institute"}
    values[field] = "2025-01"

    with pytest.raises(DomainError, match=f"{field} must be a date or None"):
        Certification(**values)


def test_certification_rejects_expiration_before_issue() -> None:
    with pytest.raises(DomainError, match="expiration_date cannot be before issue_date"):
        Certification(
            "Example Certification",
            "Example Institute",
            date(2025, 1, 1),
            date(2024, 1, 1),
        )


def test_certification_accepts_partial_dates_and_same_date() -> None:
    issue_date = date(2025, 1, 1)

    only_issue = Certification("Example Certification", "Example Institute", issue_date)
    only_expiration = Certification(
        "Example Certification", "Example Institute", expiration_date=issue_date
    )
    same_date = Certification(
        "Example Certification", "Example Institute", issue_date, issue_date
    )

    assert only_issue.issue_date == issue_date
    assert only_issue.expiration_date is None
    assert only_expiration.issue_date is None
    assert only_expiration.expiration_date == issue_date
    assert same_date.issue_date == same_date.expiration_date == issue_date


@pytest.mark.parametrize("field", ["credential_id", "credential_url"])
@pytest.mark.parametrize("value", ["", "   "])
def test_certification_rejects_empty_optional_strings(field: str, value: str) -> None:
    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        Certification("Example Certification", "Example Institute", **{field: value})


def test_certification_is_immutable() -> None:
    certification = Certification("Example Certification", "Example Institute")

    with pytest.raises(FrozenInstanceError):
        certification.name = "Other Certification"
