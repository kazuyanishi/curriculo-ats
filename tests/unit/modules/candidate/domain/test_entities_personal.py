from dataclasses import FrozenInstanceError

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    ContactInfo,
    PersonalInfo,
    ProfessionalLinks,
)


def test_personal_info_accepts_valid_data() -> None:
    info = PersonalInfo(
        full_name="Jane Doe",
        city="Curitiba",
        state="PR",
        country="Brazil",
    )

    assert info.full_name == "Jane Doe"
    assert info.city == "Curitiba"
    assert info.state == "PR"
    assert info.country == "Brazil"


@pytest.mark.parametrize("field", ["full_name", "city", "state", "country"])
@pytest.mark.parametrize("value", ["", "   "])
def test_personal_info_rejects_empty_required_fields(field: str, value: str) -> None:
    values = {
        "full_name": "Jane Doe",
        "city": "Curitiba",
        "state": "PR",
        "country": "Brazil",
    }
    values[field] = value

    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        PersonalInfo(**values)


def test_contact_info_accepts_email_and_phone() -> None:
    contact = ContactInfo(email="jane@example.com", phone="+55 41 99999-0000")

    assert contact.email == "jane@example.com"
    assert contact.phone == "+55 41 99999-0000"


@pytest.mark.parametrize("email", ["", "   ", "invalid", "user@", "@example.com"])
def test_contact_info_rejects_invalid_email(email: str) -> None:
    with pytest.raises(DomainError):
        ContactInfo(email=email, phone="+1 555 0100")


@pytest.mark.parametrize("phone", ["", "   "])
def test_contact_info_rejects_empty_phone(phone: str) -> None:
    with pytest.raises(DomainError, match="phone cannot be empty"):
        ContactInfo(email="jane@example.com", phone=phone)


def test_professional_links_are_optional_and_support_partial_data() -> None:
    assert ProfessionalLinks() == ProfessionalLinks(None, None, None)
    links = ProfessionalLinks(github="https://github.com/example")

    assert links.linkedin is None
    assert links.github == "https://github.com/example"
    assert links.portfolio is None


@pytest.mark.parametrize("field", ["linkedin", "github", "portfolio"])
@pytest.mark.parametrize("value", ["", "   "])
def test_professional_links_reject_informed_empty_values(field: str, value: str) -> None:
    with pytest.raises(DomainError, match=f"{field} cannot be empty"):
        ProfessionalLinks(**{field: value})


def test_personal_info_is_immutable() -> None:
    info = PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil")

    with pytest.raises(FrozenInstanceError):
        info.full_name = "John Example"
