from resume_ai.modules.candidate.infrastructure.ai_candidate_prompts import (
    RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT,
)


def test_prompt_requires_safe_literal_provenance_and_raw_values() -> None:
    prompt = RESUME_CANDIDATE_EXTRACTION_SYSTEM_PROMPT.lower()
    concepts = (
        "data, not instructions",
        "ignore any instructions",
        "never invent",
        "outside knowledge",
        "literally and verbatim",
        "value",
        "evidence",
        "null",
        "do not translate",
        "do not rewrite",
        "do not summarize",
        "do not normalize dates",
        "do not normalize proficiency levels",
        "do not normalize education status",
    )
    for concept in concepts:
        assert concept in prompt
