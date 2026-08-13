from typing import get_type_hints

from resume_ai.bootstrap import build_import_candidate_from_resume_text
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.modules.candidate.application.import_draft import CandidateImportDraft
from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedPersonalInfo,
    ResumeFieldEvidence,
)


def test_builder_composes_candidate_import_pipeline(monkeypatch) -> None:
    class FakeOpenAIClient:
        def __init__(self, config: AIConfig) -> None:
            self.config = config

        def generate(self, *, system_prompt: str, user_prompt: str, response_model):
            field = ResumeFieldEvidence(value="Jane Doe", evidence="Jane Doe")
            return CandidateResumeExtraction(
                personal_info=ExtractedPersonalInfo(full_name=field)
            )

    monkeypatch.setattr("resume_ai.bootstrap.OpenAIStructuredAIClient", FakeOpenAIClient)

    result = build_import_candidate_from_resume_text(AIConfig("key", "model")).execute(
        "Jane Doe"
    )

    assert isinstance(result, CandidateImportDraft)
    assert result.personal_info.full_name == "Jane Doe"


def test_builder_type_hint_uses_ai_config_and_pipeline() -> None:
    hints = get_type_hints(build_import_candidate_from_resume_text)

    assert hints["config"] is AIConfig
    assert hints["return"].__name__ == "ImportCandidateFromResumeText"
