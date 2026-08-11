from resume_ai.core.config import AppConfig
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.integrations.ai.openai_client import OpenAIStructuredAIClient
from resume_ai.modules.candidate.application.services import LoadCandidate
from resume_ai.modules.candidate.infrastructure.json_repository import (
    JsonCandidateRepository,
)
from resume_ai.modules.jobs.application.services import ExtractJobCriteria, LoadJob
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate
from resume_ai.modules.jobs.infrastructure.ai_extractor import AIJobCriteriaExtractor
from resume_ai.modules.jobs.infrastructure.text_repository import TextJobRepository
from resume_ai.modules.matching.application.matchers import DeterministicCandidateJobMatcher
from resume_ai.modules.matching.application.services import MatchCandidateToJob
from resume_ai.modules.matching.domain.services import ExactCandidateCriterionMatcher


def build_load_candidate(config: AppConfig) -> LoadCandidate:
    candidate_path = config.data_dir / "candidate" / "resume_master.json"
    repository = JsonCandidateRepository(candidate_path)
    return LoadCandidate(repository)


def build_load_job(config: AppConfig) -> LoadJob:
    job_path = config.data_dir / "jobs" / "job.txt"
    repository = TextJobRepository(job_path)
    return LoadJob(repository)


def build_extract_job_criteria(config: AIConfig) -> ExtractJobCriteria:
    client = OpenAIStructuredAIClient(config)
    extractor = AIJobCriteriaExtractor(client)
    truth_gate = JobCriteriaTruthGate()
    return ExtractJobCriteria(extractor, truth_gate)


def build_match_candidate_to_job() -> MatchCandidateToJob:
    criterion_matcher = ExactCandidateCriterionMatcher()
    matcher = DeterministicCandidateJobMatcher(criterion_matcher)
    return MatchCandidateToJob(matcher)
