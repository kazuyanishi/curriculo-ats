from resume_ai.core.config import AppConfig
from resume_ai.modules.candidate.application.services import LoadCandidate
from resume_ai.modules.candidate.infrastructure.json_repository import (
    JsonCandidateRepository,
)


def build_load_candidate(config: AppConfig) -> LoadCandidate:
    candidate_path = config.data_dir / "candidate" / "resume_master.json"
    repository = JsonCandidateRepository(candidate_path)
    return LoadCandidate(repository)
