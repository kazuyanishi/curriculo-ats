from resume_ai.core.config import AppConfig
from resume_ai.modules.candidate.application.services import LoadCandidate
from resume_ai.modules.candidate.infrastructure.json_repository import (
    JsonCandidateRepository,
)
from resume_ai.modules.jobs.application.services import LoadJob
from resume_ai.modules.jobs.infrastructure.text_repository import TextJobRepository


def build_load_candidate(config: AppConfig) -> LoadCandidate:
    candidate_path = config.data_dir / "candidate" / "resume_master.json"
    repository = JsonCandidateRepository(candidate_path)
    return LoadCandidate(repository)


def build_load_job(config: AppConfig) -> LoadJob:
    job_path = config.data_dir / "jobs" / "job.txt"
    repository = TextJobRepository(job_path)
    return LoadJob(repository)
