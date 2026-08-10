from dataclasses import fields as dataclass_fields

import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import (
    ContactInfoInput,
    PersonalInfoInput,
    ProfessionalLinksInput,
)
from resume_ai.modules.candidate.domain.entities import (
    ContactInfo,
    PersonalInfo,
    ProfessionalLinks,
)


def test_personal_info_input_accepts_valid_data_and_preserves_strings() -> None:
    schema = PersonalInfoInput(
        full_name="  Jane Doe  ",
        city="  Curitiba  ",
        state="PR",
        country="Brazil",
    )

    assert schema.full_name == "  Jane Doe  "
    assert schema.city == "  Curitiba  "
    assert isinstance(schema.to_domain(), PersonalInfo)
    assert schema.to_domain().full_name == "  Jane Doe  "


@pytest.mark.parametrize("field", ["full_name", "city", "state", "country"])
def test_personal_info_input_rejects_missing_field(field: str) -> None:
    values = {
        "full_name": "Jane Doe",
        "city": "Curitiba",
        "state": "PR",
        "country": "Brazil",
    }
    values.pop(field)

    with pytest.raises(ValidationError):
        PersonalInfoInput(**values)


@pytest.mark.parametrize("field", ["full_name", "city", "state", "country"])
@pytest.mark.parametrize("value", ["", "   "])
def test_personal_info_input_rejects_blank_field(field: str, value: str) -> None:
    values = {
        "full_name": "Jane Doe",
        "city": "Curitiba",
        "state": "PR",
        "country": "Brazil",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        PersonalInfoInput(**values)


def test_personal_info_input_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        PersonalInfoInput(
            full_name="Jane Doe",
            city="Curitiba",
            state="PR",
            country="Brazil",
            unexpected="value",
        )


def test_input_schema_is_frozen() -> None:
    schema = PersonalInfoInput(
        full_name="Jane Doe", city="Curitiba", state="PR", country="Brazil"
    )

    with pytest.raises(ValidationError):
        schema.city = "Other City"


def test_contact_info_input_validates_email_and_preserves_phone() -> None:
    schema = ContactInfoInput(email="jane@example.com", phone="+55 (41) 99999-0000")
    domain = schema.to_domain()

    assert isinstance(domain, ContactInfo)
    assert domain.email == "jane@example.com"
    assert domain.phone == "+55 (41) 99999-0000"


@pytest.mark.parametrize("field", ["email", "phone"])
def test_contact_info_input_rejects_missing_field(field: str) -> None:
    values = {"email": "jane@example.com", "phone": "+55 41 99999-0000"}
    values.pop(field)

    with pytest.raises(ValidationError):
        ContactInfoInput(**values)


@pytest.mark.parametrize("email", ["", "   ", "invalid", "user@", "@example.com"])
def test_contact_info_input_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        ContactInfoInput(email=email, phone="+55 41 99999-0000")


@pytest.mark.parametrize("phone", ["", "   "])
def test_contact_info_input_rejects_blank_phone(phone: str) -> None:
    with pytest.raises(ValidationError):
        ContactInfoInput(email="jane@example.com", phone=phone)


def test_professional_links_input_defaults_to_empty_links() -> None:
    schema = ProfessionalLinksInput()
    domain = schema.to_domain()

    assert schema.linkedin is None
    assert schema.github is None
    assert schema.portfolio is None
    assert isinstance(domain, ProfessionalLinks)
    assert domain == ProfessionalLinks()


@pytest.mark.parametrize("field", ["linkedin", "github", "portfolio"])
def test_professional_links_input_accepts_explicit_none(field: str) -> None:
    schema = ProfessionalLinksInput(**{field: None})

    assert getattr(schema, field) is None


def test_professional_links_input_accepts_all_explicit_none_and_preserves_domain() -> None:
    schema = ProfessionalLinksInput(
        linkedin=None,
        github=None,
        portfolio=None,
    )

    domain = schema.to_domain()

    assert domain == ProfessionalLinks(
        linkedin=None,
        github=None,
        portfolio=None,
    )


def test_professional_links_input_accepts_partial_links_and_preserves_values() -> None:
    schema = ProfessionalLinksInput(github="https://Example.com/Profile")

    assert schema.github == "https://Example.com/Profile"
    assert schema.to_domain().github == "https://Example.com/Profile"


@pytest.mark.parametrize("field", ["linkedin", "github", "portfolio"])
@pytest.mark.parametrize("value", ["", "   "])
def test_professional_links_input_rejects_blank_links(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        ProfessionalLinksInput(**{field: value})


def test_domain_entities_remain_dataclasses() -> None:
    assert {field.name for field in dataclass_fields(PersonalInfo)} == {
        "full_name",
        "city",
        "state",
        "country",
    }
    assert {field.name for field in dataclass_fields(ContactInfo)} == {"email", "phone"}
    assert {field.name for field in dataclass_fields(ProfessionalLinks)} == {
        "linkedin",
        "github",
        "portfolio",
    }
