import json

import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.schemas import CandidateInput
from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    EducationStatus,
    Experience,
    LanguageLevel,
    ProficiencyLevel,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth


def _minimum_json() -> str:
    return json.dumps(
        {
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
    )


def _complete_json() -> str:
    return json.dumps(
        {
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
            "professional_links": {
                "linkedin": None,
                "github": "https://github.com/example",
                "portfolio": None,
            },
            "experiences": [
                {
                    "company": "Example Systems",
                    "role": "Support Analyst",
                    "start_date": "2024-01",
                    "end_date": None,
                    "activities": [{"description": "Provided technical support"}],
                    "achievements": [{"description": "Improved response workflow"}],
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
            "skills": [
                {"name": "Second", "level": "advanced"},
                {"name": "Communication", "level": None},
                {"name": "Communication", "level": None},
            ],
            "technologies": [{"name": "Python", "level": "advanced"}],
            "tools": [{"name": "Git", "level": "intermediate"}],
            "languages": [{"name": "English", "level": "fluent"}],
            "certifications": [
                {
                    "name": "Example Certification",
                    "issuer": "Example Institute",
                    "issue_date": "2025-01-01",
                    "expiration_date": None,
                    "credential_id": None,
                    "credential_url": None,
                }
            ],
            "projects": [
                {
                    "name": "Example Project",
                    "description": "Example project description",
                    "start_date": "2024-01",
                    "end_date": None,
                    "technologies": ["Python", "FastAPI"],
                    "url": None,
                }
            ],
        },
        ensure_ascii=False,
    )


def test_minimum_json_becomes_candidate() -> None:
    schema = CandidateInput.model_validate_json(_minimum_json())
    candidate = schema.to_domain()

    assert isinstance(candidate, Candidate)
    assert candidate.personal_info.full_name == "Jane Doe"
    assert candidate.experiences == ()


def test_complete_json_converts_nested_data_to_domain() -> None:
    schema = CandidateInput.model_validate_json(_complete_json())
    candidate = schema.to_domain()

    assert isinstance(candidate, Candidate)
    assert isinstance(candidate.experiences[0], Experience)
    assert isinstance(candidate.experiences[0].activities[0], Activity)
    assert candidate.experiences[0].start_date == YearMonth("2024-01")
    assert candidate.education[0].status is EducationStatus.COMPLETED
    assert candidate.technologies[0].level is ProficiencyLevel.ADVANCED
    assert candidate.languages[0].level is LanguageLevel.FLUENT
    assert candidate.projects[0].technologies == ("Python", "FastAPI")
    assert all(isinstance(collection, tuple) for collection in (
        candidate.experiences,
        candidate.education,
        candidate.skills,
        candidate.technologies,
        candidate.tools,
        candidate.languages,
        candidate.certifications,
        candidate.projects,
    ))
    assert [skill.name for skill in candidate.skills] == [
        "Second",
        "Communication",
        "Communication",
    ]


@pytest.mark.parametrize("root", ["[]", '"resume"', "123", "null"])
def test_json_root_must_be_an_object(root: str) -> None:
    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json(root)


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json('{"personal_info":')


def test_top_level_extra_is_rejected() -> None:
    payload = json.loads(_minimum_json())
    payload["score"] = 100

    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json(json.dumps(payload))


def test_nested_extra_is_rejected() -> None:
    payload = json.loads(_minimum_json())
    payload["skills"] = [{"name": "Communication", "score": 100}]

    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize("field", ["personal_info", "contact_info"])
def test_required_top_level_field_is_rejected_when_missing(field: str) -> None:
    payload = json.loads(_minimum_json())
    payload.pop(field)

    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json(json.dumps(payload))


def test_professional_links_null_is_rejected() -> None:
    payload = json.loads(_minimum_json())
    payload["professional_links"] = None

    with pytest.raises(ValidationError):
        CandidateInput.model_validate_json(json.dumps(payload))


def test_optional_nulls_are_accepted() -> None:
    schema = CandidateInput.model_validate_json(_complete_json())

    assert schema.professional_links.linkedin is None
    assert schema.skills[1].level is None
    assert schema.certifications[0].credential_id is None
    assert schema.certifications[0].credential_url is None
    assert schema.projects[0].url is None


def test_utf8_json_is_preserved() -> None:
    payload = json.loads(_minimum_json())
    payload["personal_info"]["city"] = "São José"

    schema = CandidateInput.model_validate_json(
        json.dumps(payload, ensure_ascii=False)
    )

    assert schema.personal_info.city == "São José"
