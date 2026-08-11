from pathlib import Path
from typing import get_type_hints

import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.jobs.domain.repositories import JobRepository
from resume_ai.modules.jobs.infrastructure.text_repository import TextJobRepository


def _write_job(tmp_path: Path, content: bytes) -> Path:
    path = tmp_path / "job.txt"
    path.write_bytes(content)
    return path


def _load_job(repository: JobRepository) -> JobPosting:
    return repository.get()


def test_text_job_repository_reads_complete_utf8_content(tmp_path: Path) -> None:
    content = "  Senior Python Developer\n\nRequisitos:\n- São José\n- Português  "
    path = _write_job(tmp_path, content.encode("utf-8"))

    job = TextJobRepository(path).get()

    assert isinstance(job, JobPosting)
    assert job.description == content
    assert job.title is None
    assert job.company is None
    assert job.location is None
    assert job.source_url is None


@pytest.mark.parametrize("content", [b"Line one\r\nLine two\r\n", b"Line one\nLine two\n"])
def test_text_job_repository_preserves_line_endings(
    tmp_path: Path, content: bytes
) -> None:
    path = _write_job(tmp_path, content)

    job = TextJobRepository(path).get()

    assert job.description == content.decode("utf-8")


def test_text_job_repository_does_not_parse_first_line_as_title(tmp_path: Path) -> None:
    content = "Senior Backend Developer\nPython and PostgreSQL required."
    path = _write_job(tmp_path, content.encode("utf-8"))

    job = TextJobRepository(path).get()

    assert job.description == content
    assert job.title is None


@pytest.mark.parametrize("content", [b"", b" \n\t "])
def test_text_job_repository_delegates_blank_validation_to_domain(
    tmp_path: Path, content: bytes
) -> None:
    path = _write_job(tmp_path, content)

    with pytest.raises(DomainError):
        TextJobRepository(path).get()


def test_text_job_repository_propagates_missing_file_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.txt"
    repository = TextJobRepository(path)

    with pytest.raises(FileNotFoundError):
        repository.get()

    assert not path.exists()


def test_text_job_repository_propagates_invalid_utf8(tmp_path: Path) -> None:
    path = _write_job(tmp_path, b"Python \xff")

    with pytest.raises(UnicodeDecodeError):
        TextJobRepository(path).get()


def test_text_job_repository_reads_current_content_on_each_get(tmp_path: Path) -> None:
    path = _write_job(tmp_path, b"First job")
    repository = TextJobRepository(path)

    first = repository.get()
    path.write_bytes(b"Second job")
    second = repository.get()

    assert first.description == "First job"
    assert second.description == "Second job"


def test_text_job_repository_is_structurally_compatible_with_job_repository(
    tmp_path: Path,
) -> None:
    path = _write_job(tmp_path, b"Example job")

    job = _load_job(TextJobRepository(path))

    assert job.description == "Example job"


def test_text_job_repository_type_hints() -> None:
    assert get_type_hints(TextJobRepository.get)["return"] is JobPosting
    assert get_type_hints(TextJobRepository.__init__)["path"] is Path
