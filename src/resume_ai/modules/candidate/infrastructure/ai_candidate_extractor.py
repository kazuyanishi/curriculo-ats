from resume_ai.integrations.ai.client import StructuredAIClient
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction
from resume_ai.modules.candidate.infrastructure.ai_candidate_prompts import (
    RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT,
)
from resume_ai.modules.candidate.infrastructure.resume_extraction_heuristics import (
    enrich_extraction,
)


class AIResumeCandidateExtractor:
    def __init__(self, client: StructuredAIClient) -> None:
        self._client = client

    def extract(self, resume_text: str) -> CandidateResumeExtraction:
        extraction = self._client.generate(
            system_prompt=RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=resume_text,
            response_model=CandidateResumeExtraction,
        )
        return enrich_extraction(resume_text, extraction)
