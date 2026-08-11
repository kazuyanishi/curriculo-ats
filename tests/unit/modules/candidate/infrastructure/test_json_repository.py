from datetime import date
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    Language,
    LanguageLevel,
    ProficiencyLevel,
)
from resume_ai.modules.candidate.domain.repositories import CandidateRepository
from resume_ai.modules.candidate.infrastructure.json_repository import (
    JsonCandidateRepository,
)


def _write_json(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "resume.json"
    path.write_text(content, encoding="utf-8")
    return path


def _minimum_json() -> str:
    return """
    {
      "personal_info": {
        "full_name": "Jane Doe",
        "city": "Curitiba",
        "state": "PR",
        "country": "Brazil"
      },
      "contact_info": {
        "email": "jane@example.com",
        "phone": "+55 41 99999-0000"
      }
    }
    """


def _nested_json() -> str:
    return """
    {
      "personal_info": {
        "full_name": "  Jane Doe  ",
        "city": "São José",
        "state": "PR",
        "country": "Brazil"
      },
      "contact_info": {
        "email": "jane@example.com",
        "phone": "+55 41 99999-0000"
      },
      "experiences": [
        {
          "company": "Example Systems",
          "role": "Support Analyst",
          "start_date": "2024-01-01",
          "activities": [{"description": "  Provided support  "}],
          "achievements": [{"description": "Improved workflow"}]
        }
      ],
      "technologies": [{"name": "Python", "level": "advanced"}],
      "languages": [{"name": "Português", "level": "fluent"}],
      "projects": [
        {
          "name": "Example Project",
          "description": "Example project description",
          "start_date": "2024-01-01",
          "technologies": ["Python", "FastAPI"]
        }
      ]
    }
    """


def _load(repository: CandidateRepository) -> Candidate:
    return repository.get()


def test_json_repository_loads_minimum_candidate(tmp_path: Path) -> None:
    repository = JsonCandidateRepository(_write_json(tmp_path, _minimum_json()))

    candidate = repository.get()

    assert isinstance(candidate, Candidate)
    assert candidate.personal_info.full_name == "Jane Doe"


def test_json_repository_satisfies_structural_repository_contract(tmp_path: Path) -> None:
    repository = JsonCandidateRepository(_write_json(tmp_path, _minimum_json()))

    candidate = _load(repository)

    assert isinstance(candidate, Candidate)


def test_json_repository_converts_nested_domain_data(tmp_path: Path) -> None:
    repository = JsonCandidateRepository(_write_json(tmp_path, _nested_json()))

    candidate = repository.get()

    assert candidate.personal_info.full_name == "  Jane Doe  "
    assert candidate.personal_info.city == "São José"
    assert isinstance(candidate.experiences[0].activities[0], Activity)
    assert candidate.experiences[0].start_date == date(2024, 1, 1)
    assert candidate.technologies[0].level is ProficiencyLevel.ADVANCED
    assert isinstance(candidate.languages[0], Language)
    assert candidate.languages[0].level is LanguageLevel.FLUENT
    assert candidate.projects[0].technologies == ("Python", "FastAPI")
    assert isinstance(candidate, Candidate)
    assert not isinstance(candidate, BaseModel)


def test_json_repository_rereads_file_on_each_get(tmp_path: Path) -> None:
    path = _write_json(tmp_path, _minimum_json())
    repository = JsonCandidateRepository(path)

    assert repository.get().personal_info.full_name == "Jane Doe"

    path.write_text(_minimum_json().replace("Jane Doe", "John Doe"), encoding="utf-8")

    assert repository.get().personal_info.full_name == "John Doe"


def test_json_repository_propagates_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    repository = JsonCandidateRepository(path)

    with pytest.raises(FileNotFoundError):
        repository.get()

    assert not path.exists()


def test_json_repository_rejects_malformed_json(tmp_path: Path) -> None:
    repository = JsonCandidateRepository(_write_json(tmp_path, '{"personal_info":'))

    with pytest.raises(ValidationError):
        repository.get()


def test_json_repository_rejects_invalid_schema(tmp_path: Path) -> None:
    repository = JsonCandidateRepository(
        _write_json(tmp_path, '{"personal_info": {"full_name": "Jane Doe"}}')
    )

    with pytest.raises(ValidationError):
        repository.get()


def test_json_repository_propagates_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_bytes(b'{"personal_info":\xff}')
    repository = JsonCandidateRepository(path)

    with pytest.raises(UnicodeDecodeError):
        repository.get()
