from dataclasses import dataclass

from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.documents.application.ports import CandidateDocumentRenderer


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    filename: str
    media_type: str
    content: bytes

    def __post_init__(self) -> None:
        if not self.filename:
            raise ValueError("filename must not be empty")
        if not self.media_type:
            raise ValueError("media_type must not be empty")
        if not isinstance(self.content, bytes) or not self.content:
            raise ValueError("content must be non-empty bytes")


@dataclass(frozen=True, slots=True)
class GeneratedCandidateDocuments:
    docx: GeneratedDocument
    pdf: GeneratedDocument


class GenerateCandidateDocuments:
    def __init__(
        self,
        docx_renderer: CandidateDocumentRenderer,
        pdf_renderer: CandidateDocumentRenderer,
    ) -> None:
        self._docx_renderer = docx_renderer
        self._pdf_renderer = pdf_renderer

    def execute(self, candidate: Candidate) -> GeneratedCandidateDocuments:
        return GeneratedCandidateDocuments(
            docx=GeneratedDocument(
                filename="resume.docx",
                media_type=(
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ),
                content=self._docx_renderer.render(candidate),
            ),
            pdf=GeneratedDocument(
                filename="resume.pdf",
                media_type="application/pdf",
                content=self._pdf_renderer.render(candidate),
            ),
        )
