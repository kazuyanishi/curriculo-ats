from datetime import date, datetime

import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import CertificationInput
from resume_ai.modules.candidate.domain.entities import Certification


def test_certification_minimum_defaults_optional_fields() -> None:
    schema = CertificationInput(name="Example Certification", issuer="Example Institute")

    assert schema.issue_date is None
    assert schema.expiration_date is None
    assert schema.credential_id is None
    assert schema.credential_url is None


def test_certification_accepts_dates_and_converts_to_domain() -> None:
    schema = CertificationInput(
        name="  AWS Certified  ",
        issuer="  AWS  ",
        issue_date="2025-01-01",
        expiration_date="2028-01-01",
        credential_id="  ABC-123  ",
        credential_url="https://Example.com/Credential",
    )
    domain = schema.to_domain()

    assert isinstance(domain, Certification)
    assert domain.name == "  AWS Certified  "
    assert domain.issuer == "  AWS  "
    assert domain.issue_date == date(2025, 1, 1)
    assert domain.expiration_date == date(2028, 1, 1)
    assert domain.credential_id == "  ABC-123  "
    assert domain.credential_url == "https://Example.com/Credential"


@pytest.mark.parametrize("field", ["name", "issuer"])
@pytest.mark.parametrize("value", ["", "   "])
def test_certification_rejects_blank_required_text(field: str, value: str) -> None:
    values = {"name": "Certification", "issuer": "Institute"}
    values[field] = value

    with pytest.raises(ValidationError):
        CertificationInput(**values)


@pytest.mark.parametrize("field", ["credential_id", "credential_url"])
def test_certification_accepts_explicit_none_credentials(field: str) -> None:
    schema = CertificationInput(
        name="Certification",
        issuer="Institute",
        **{field: None},
    )

    assert getattr(schema, field) is None


@pytest.mark.parametrize("field", ["credential_id", "credential_url"])
@pytest.mark.parametrize("value", ["", "   "])
def test_certification_rejects_blank_credentials(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        CertificationInput(name="Certification", issuer="Institute", **{field: value})


@pytest.mark.parametrize(
    "value",
    ["2025-01", "01/2025", "20250101", 123, datetime(2025, 1, 1)],
)
def test_certification_rejects_invalid_dates(value) -> None:
    with pytest.raises(ValidationError):
        CertificationInput(name="Certification", issuer="Institute", issue_date=value)


def test_certification_rejects_expiration_before_issue() -> None:
    with pytest.raises(ValidationError):
        CertificationInput(
            name="Certification",
            issuer="Institute",
            issue_date="2025-01-02",
            expiration_date="2025-01-01",
        )


def test_certification_accepts_partial_dates() -> None:
    assert CertificationInput(
        name="Certification", issuer="Institute", issue_date="2025-01-01"
    ).expiration_date is None
    assert CertificationInput(
        name="Certification", issuer="Institute", expiration_date="2028-01-01"
    ).issue_date is None
