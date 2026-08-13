
import pytest
from pydantic import BaseModel, ValidationError

from resume_ai.modules.candidate.application.schemas import (
    CandidateInput,
    ContactInfoInput,
    PersonalInfoInput,
    ProfessionalLinksInput,
)
from resume_ai.modules.candidate.domain.entities import (
    Activity,
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
from resume_ai.modules.candidate.domain.value_objects import YearMonth


def _minimum_data() -> dict[str, object]:
    return {
        "personal_info": {
            "full_name": "Jane Doe",
            "city": "Curitiba",
            "state": "PR",
            "country": "Brazil",
        },
        "contact_info": {
            "email": "jane@example.com",
            "phone": "+55 41 99999-0000",
        },
    }


def test_candidate_input_accepts_minimum_external_data() -> None:
    schema = CandidateInput(**_minimum_data())

    assert isinstance(schema.personal_info, PersonalInfoInput)
    assert isinstance(schema.contact_info, ContactInfoInput)
    assert isinstance(schema.professional_links, ProfessionalLinksInput)
    assert schema.professional_links == ProfessionalLinksInput()
    assert schema.experiences == ()
    assert schema.education == ()
    assert schema.skills == ()
    assert schema.technologies == ()
    assert schema.tools == ()
    assert schema.languages == ()
    assert schema.certifications == ()
    assert schema.projects == ()

    candidate = schema.to_domain()
    assert isinstance(candidate, Candidate)
    assert candidate.professional_links == ProfessionalLinks()
    assert candidate.experiences == ()
    assert candidate.projects == ()


def test_candidate_input_converts_complete_resume_to_domain() -> None:
    data = _minimum_data()
    data.update(
        {
            "professional_links": {"github": "https://github.com/example"},
            "experiences": [
                {
                    "company": "Example Systems",
                    "role": "Support Analyst",
                    "start_date": "2024-01",
                    "activities": [{"description": "Provided support"}],
                    "achievements": [{"description": "Improved response time"}],
                }
            ],
            "education": [
                {
                    "institution": "Example University",
                    "course": "Computer Science",
                    "status": "completed",
                    "start_date": "2020-01",
                    "end_date": "2024-01",
                }
            ],
            "skills": [{"name": "Communication", "level": "advanced"}],
            "technologies": [{"name": "Python", "level": "advanced"}],
            "tools": [{"name": "Git", "level": "advanced"}],
            "languages": [{"name": "English", "level": "fluent"}],
            "certifications": [
                {
                    "name": "Example Certification",
                    "issuer": "Example Institute",
                    "issue_date": "2025-01-01",
                }
            ],
            "projects": [
                {
                    "name": "Example Project",
                    "description": "Example description",
                    "start_date": "2024-02",
                    "technologies": ["Python", "FastAPI"],
                }
            ],
        }
    )

    schema = CandidateInput(**data)
    candidate = schema.to_domain()

    assert isinstance(candidate, Candidate)
    assert isinstance(candidate.personal_info, PersonalInfo)
    assert isinstance(candidate.contact_info, ContactInfo)
    assert isinstance(candidate.professional_links, ProfessionalLinks)
    assert isinstance(candidate.experiences[0], Experience)
    assert isinstance(candidate.experiences[0].activities[0], Activity)
    assert isinstance(candidate.education[0], Education)
    assert isinstance(candidate.skills[0], Skill)
    assert isinstance(candidate.technologies[0], Technology)
    assert isinstance(candidate.tools[0], Tool)
    assert isinstance(candidate.languages[0], Language)
    assert isinstance(candidate.certifications[0], Certification)
    assert isinstance(candidate.projects[0], Project)
    assert candidate.experiences[0].start_date == YearMonth("2024-01")
    assert candidate.education[0].status is EducationStatus.COMPLETED
    assert candidate.technologies[0].level is ProficiencyLevel.ADVANCED
    assert candidate.languages[0].level is LanguageLevel.FLUENT
    assert candidate.projects[0].technologies == ("Python", "FastAPI")
    assert not isinstance(candidate.experiences[0], BaseModel)


def test_candidate_input_external_lists_become_tuples() -> None:
    data = _minimum_data()
    data.update(
        {
            "experiences": [
                {"company": "Example", "role": "Analyst", "start_date": "2024-01"}
            ],
            "education": [
                {"institution": "University", "course": "Course", "status": "completed"}
            ],
            "skills": [{"name": "One"}],
            "technologies": [{"name": "Two"}],
            "tools": [{"name": "Three"}],
            "languages": [{"name": "Four"}],
            "certifications": [{"name": "Five", "issuer": "Institute"}],
            "projects": [{"name": "Six", "description": "Description"}],
        }
    )
    schema = CandidateInput(**data)

    assert isinstance(schema.experiences, tuple)
    assert isinstance(schema.education, tuple)
    assert isinstance(schema.skills, tuple)
    assert isinstance(schema.technologies, tuple)
    assert isinstance(schema.tools, tuple)
    assert isinstance(schema.languages, tuple)
    assert isinstance(schema.certifications, tuple)
    assert isinstance(schema.projects, tuple)


def test_candidate_input_preserves_order_and_duplicates() -> None:
    data = _minimum_data()
    data["skills"] = [{"name": "Second"}, {"name": "First"}, {"name": "First"}]

    schema = CandidateInput(**data)
    candidate = schema.to_domain()

    assert [item.name for item in schema.skills] == ["Second", "First", "First"]
    assert [item.name for item in candidate.skills] == ["Second", "First", "First"]


@pytest.mark.parametrize("field", ["personal_info", "contact_info"])
def test_candidate_input_requires_identity_fields(field: str) -> None:
    data = _minimum_data()
    data.pop(field)

    with pytest.raises(ValidationError):
        CandidateInput(**data)


@pytest.mark.parametrize("field", ["personal_info", "contact_info"])
def test_candidate_input_rejects_none_identity_fields(field: str) -> None:
    data = _minimum_data()
    data[field] = None

    with pytest.raises(ValidationError):
        CandidateInput(**data)


def test_candidate_input_rejects_explicit_none_links() -> None:
    data = _minimum_data()
    data["professional_links"] = None

    with pytest.raises(ValidationError):
        CandidateInput(**data)


def test_candidate_input_default_factory_creates_independent_links() -> None:
    candidate_a = CandidateInput(**_minimum_data())
    candidate_b = CandidateInput(**_minimum_data())

    assert candidate_a.professional_links is not candidate_b.professional_links


def test_candidate_input_rejects_primitive_and_domain_items() -> None:
    primitive_data = _minimum_data()
    primitive_data["skills"] = ["Communication"]
    with pytest.raises(ValidationError):
        CandidateInput(**primitive_data)

    domain_data = _minimum_data()
    domain_data["skills"] = [Skill("Communication")]
    with pytest.raises(ValidationError):
        CandidateInput(**domain_data)


def test_candidate_input_rejects_top_level_and_nested_extra() -> None:
    top_level_data = _minimum_data()
    top_level_data["score"] = 100
    with pytest.raises(ValidationError):
        CandidateInput(**top_level_data)

    nested_data = _minimum_data()
    nested_data["skills"] = [{"name": "Communication", "unknown": True}]
    with pytest.raises(ValidationError):
        CandidateInput(**nested_data)
