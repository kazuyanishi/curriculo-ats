from typing import Protocol

from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction


class ResumeTextExtractor(Protocol):
    def extract(self, content: bytes) -> str:
        ...


class ResumeCandidateExtractor(Protocol):
    def extract(self, resume_text: str) -> CandidateResumeExtraction:
        ...
