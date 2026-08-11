from pathlib import Path

from resume_ai.modules.candidate.application.schemas import CandidateInput
from resume_ai.modules.candidate.domain.entities import Candidate


class JsonCandidateRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def get(self) -> Candidate:
        content = self._path.read_text(encoding="utf-8")
        schema = CandidateInput.model_validate_json(content)
        return schema.to_domain()
