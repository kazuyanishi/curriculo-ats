from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    Certification,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
    Language,
    LanguageLevel,
    PersonalInfo,
    ProfessionalLinks,
    ProficiencyLevel,
    Project,
    Skill,
    Technology,
    Tool,
)


def _personal_info() -> PersonalInfo:
    return PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil")


def _contact_info() -> ContactInfo:
    return ContactInfo("jane@example.com", "+55 41 99999-0000")


def _candidate_kwargs() -> dict:
    experience = Experience("Example Systems", "Support Analyst", date(2024, 1, 1))
    education = Education("Example University", "Computer Science", EducationStatus.COMPLETED)
    skill = Skill("Communication")
    technology = Technology("Python", ProficiencyLevel.ADVANCED)
    tool = Tool("Docker", ProficiencyLevel.BASIC)
    language = Language("English", LanguageLevel.INTERMEDIATE)
    certification = Certification("Example Certification", "Example Institute")
    project = Project("Example Project", "Example description.", technologies=("Python",))
    return {
        "personal_info": _personal_info(),
        "contact_info": _contact_info(),
        "professional_links": ProfessionalLinks(github="https://github.com/example"),
        "experiences": (experience,),
        "education": (education,),
        "skills": (skill,),
        "technologies": (technology,),
        "tools": (tool,),
        "languages": (language,),
        "certifications": (certification,),
        "projects": (project,),
    }


def test_candidate_minimum_uses_empty_defaults() -> None:
    personal_info = _personal_info()
    contact_info = _contact_info()
    candidate = Candidate(personal_info, contact_info)

    assert candidate.personal_info is personal_info
    assert candidate.contact_info is contact_info
    assert candidate.professional_links == ProfessionalLinks()
    assert candidate.professional_links.linkedin is None
    assert candidate.professional_links.github is None
    assert candidate.professional_links.portfolio is None
    assert candidate.experiences == ()
    assert candidate.education == ()
    assert candidate.skills == ()
    assert candidate.technologies == ()
    assert candidate.tools == ()
    assert candidate.languages == ()
    assert candidate.certifications == ()
    assert candidate.projects == ()


def test_candidate_complete_preserves_objects_and_collections() -> None:
    values = _candidate_kwargs()
    candidate = Candidate(**values)

    for field_name, value in values.items():
        assert getattr(candidate, field_name) is value

    assert all(isinstance(getattr(candidate, field_name), tuple) for field_name in (
        "experiences",
        "education",
        "skills",
        "technologies",
        "tools",
        "languages",
        "certifications",
        "projects",
    ))


def test_candidate_accepts_explicit_professional_links() -> None:
    links = ProfessionalLinks(github="https://github.com/example")

    candidate = Candidate(_personal_info(), _contact_info(), links)

    assert candidate.professional_links is links


@pytest.mark.parametrize("field_name", ["personal_info", "contact_info"])
def test_candidate_rejects_invalid_required_object(field_name: str) -> None:
    values = {"personal_info": _personal_info(), "contact_info": _contact_info()}
    values[field_name] = None

    with pytest.raises(DomainError, match=f"{field_name} must be"):
        Candidate(**values)


def test_candidate_rejects_invalid_professional_links() -> None:
    with pytest.raises(DomainError, match="professional_links must be"):
        Candidate(_personal_info(), _contact_info(), None)


@pytest.mark.parametrize(
    "field_name",
    [
        "experiences",
        "education",
        "skills",
        "technologies",
        "tools",
        "languages",
        "certifications",
        "projects",
    ],
)
def test_candidate_rejects_lists_for_all_collections(field_name: str) -> None:
    with pytest.raises(DomainError, match=f"{field_name} must be a tuple"):
        Candidate(**{field_name: []}, personal_info=_personal_info(), contact_info=_contact_info())


@pytest.mark.parametrize(
    ("field_name", "invalid_item"),
    [
        ("experiences", "Example job"),
        ("education", "Example course"),
        ("skills", Technology("Python")),
        ("technologies", Skill("Python")),
        ("tools", Technology("Docker")),
        ("languages", Skill("English")),
        ("certifications", Project("Example Project", "Example description.")),
        ("projects", Experience("Example Systems", "Analyst", date(2024, 1, 1))),
    ],
)
def test_candidate_rejects_invalid_collection_items(field_name: str, invalid_item) -> None:
    with pytest.raises(DomainError, match=f"{field_name} contains"):
        Candidate(
            _personal_info(),
            _contact_info(),
            **{field_name: (invalid_item,)},
        )


def test_candidate_preserves_duplicates_and_order() -> None:
    first = Skill("Communication")
    second = Skill("Problem solving")
    skills = (second, first, first)

    candidate = Candidate(_personal_info(), _contact_info(), skills=skills)

    assert candidate.skills == skills
    assert candidate.skills[0] is second
    assert candidate.skills[1] is first
    assert candidate.skills[2] is first


def test_candidate_is_immutable() -> None:
    candidate = Candidate(_personal_info(), _contact_info())

    with pytest.raises(FrozenInstanceError):
        candidate.personal_info = _personal_info()
