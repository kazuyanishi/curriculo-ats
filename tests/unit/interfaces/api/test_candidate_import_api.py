from io import BytesIO

import pytest
from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen.canvas import Canvas

from resume_ai.integrations.ai.config import AIConfig
from resume_ai.interfaces.api.app import create_app
from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedNamedItem,
    ExtractedPersonalInfo,
    ResumeFieldEvidence,
)


def _evidence(value: str) -> ResumeFieldEvidence:
    return ResumeFieldEvidence(value=value, evidence=value)


def _extraction() -> CandidateResumeExtraction:
    return CandidateResumeExtraction(
        personal_info=ExtractedPersonalInfo(full_name=_evidence("Jane Doe")),
        technologies=(ExtractedNamedItem(name=_evidence("Python")),),
    )


class FakeOpenAIClient:
    def __init__(self, config: AIConfig) -> None:
        self.config = config

    def generate(self, *, system_prompt: str, user_prompt: str, response_model):
        return _extraction()


class FailingOpenAIClient(FakeOpenAIClient):
    def generate(self, **kwargs: object):
        raise RuntimeError("AI failure")


class HallucinatingOpenAIClient(FakeOpenAIClient):
    def generate(self, *, system_prompt: str, user_prompt: str, response_model):
        return CandidateResumeExtraction(
            personal_info=ExtractedPersonalInfo(full_name=_evidence("Kubernetes"))
        )


def _docx_bytes(*lines: str) -> bytes:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _pdf_bytes(*lines: str) -> bytes:
    output = BytesIO()
    canvas = Canvas(output)
    for index, line in enumerate(lines):
        canvas.drawString(72, 750 - index * 20, line)
    canvas.save()
    return output.getvalue()


def _empty_pdf_bytes() -> bytes:
    output = BytesIO()
    Canvas(output).save()
    return output.getvalue()


def _client(monkeypatch, client_class=FakeOpenAIClient) -> TestClient:
    monkeypatch.setattr("resume_ai.bootstrap.OpenAIStructuredAIClient", client_class)
    return TestClient(create_app(AIConfig("key", "model")))


def test_unsupported_extension_returns_415_without_ai(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.post(
        "/api/v1/candidate/import",
        files={"file": ("resume.txt", b"Jane Doe", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported resume file type"}


def test_file_over_limit_returns_413() -> None:
    client = TestClient(create_app(AIConfig("key", "model")))

    response = client.post(
        "/api/v1/candidate/import",
        files={"file": ("resume.pdf", b"x" * (5 * 1024 * 1024 + 1), "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Resume file is too large"}


def test_empty_file_returns_422() -> None:
    response = TestClient(create_app(AIConfig("key", "model"))).post(
        "/api/v1/candidate/import",
        files={"file": ("resume.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Resume file is empty"}


@pytest.mark.parametrize("filename", ["resume.pdf", "resume.docx"])
def test_corrupted_documents_return_stable_422(filename: str) -> None:
    response = TestClient(create_app(AIConfig("key", "model"))).post(
        "/api/v1/candidate/import",
        files={"file": (filename, b"not-a-document", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Could not extract text from resume"}


def test_pdf_without_text_returns_422() -> None:
    response = TestClient(create_app(AIConfig("key", "model"))).post(
        "/api/v1/candidate/import",
        files={"file": ("resume.pdf", _empty_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Resume contains no extractable text"}


def test_missing_ai_configuration_returns_503(monkeypatch) -> None:
    monkeypatch.delenv("RESUME_AI_API_KEY", raising=False)
    monkeypatch.delenv("RESUME_AI_MODEL", raising=False)
    response = TestClient(create_app()).post(
        "/api/v1/candidate/import",
        files={
            "file": (
                "resume.docx",
                _docx_bytes("Jane Doe"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "AI configuration unavailable"}


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("resume.DOCX", "application/octet-stream", _docx_bytes("Jane Doe", "Python")),
        ("resume.PDF", "application/octet-stream", _pdf_bytes("Jane Doe", "Python")),
    ],
    ids=["docx", "pdf"],
)
def test_happy_path_accepts_pdf_and_docx_case_insensitively(
    monkeypatch,
    filename: str,
    content_type: str,
    content: bytes,
) -> None:
    response = _client(monkeypatch).post(
        "/api/v1/candidate/import",
        files={"file": (filename, content, content_type)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["personal_info"]["full_name"] == "Jane Doe"
    assert body["technologies"][0]["name"] == "Python"
    assert body["issues"]
    assert "evidence" not in response.text
    assert "resume_text" not in response.text


def test_grounding_failure_returns_stable_422(monkeypatch, caplog) -> None:
    caplog.set_level("WARNING")
    response = _client(monkeypatch, HallucinatingOpenAIClient).post(
        "/api/v1/candidate/import",
        files={"file": ("resume.docx", _docx_bytes("Python"), "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Resume extraction could not be validated"}
    assert "personal_info.full_name" not in response.text
    assert "Kubernetes" not in response.text
    assert "Python" not in response.text
    assert any(
        "path=personal_info.full_name reason=evidence_not_in_resume_text" in record.message
        for record in caplog.records
    )
    assert all("Kubernetes" not in record.message for record in caplog.records)


def test_ai_failure_returns_stable_502(monkeypatch) -> None:
    response = _client(monkeypatch, FailingOpenAIClient).post(
        "/api/v1/candidate/import",
        files={"file": ("resume.pdf", _pdf_bytes("Jane Doe"), "application/octet-stream")},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "AI integration failed"}
