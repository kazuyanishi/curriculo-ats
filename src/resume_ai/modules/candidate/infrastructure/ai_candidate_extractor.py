from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction
from resume_ai.modules.candidate.infrastructure.ai_candidate_prompts import (
    RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT,
)


class AIResumeCandidateExtractor:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def extract(self, resume_text: str) -> CandidateResumeExtraction:
        return self._client.generate(
            system_prompt=RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=resume_text,
            response_model=CandidateResumeExtraction,
        )
