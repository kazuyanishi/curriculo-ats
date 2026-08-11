from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.jobs.infrastructure.ai_prompts import (
    JOB_CRITERIA_SYSTEM_PROMPT,
    build_job_criteria_user_prompt,
)


def test_job_criteria_system_prompt_is_non_empty() -> None:
    assert isinstance(JOB_CRITERIA_SYSTEM_PROMPT, str)
    assert JOB_CRITERIA_SYSTEM_PROMPT.strip()


def test_job_criteria_system_prompt_documents_categories() -> None:
    categories = (
        "skill",
        "technology",
        "tool",
        "language",
        "education",
        "experience",
        "certification",
        "other",
    )

    assert all(category in JOB_CRITERIA_SYSTEM_PROMPT for category in categories)


def test_job_criteria_system_prompt_documents_importances() -> None:
    importances = ("required", "preferred", "unspecified")

    assert all(importance in JOB_CRITERIA_SYSTEM_PROMPT for importance in importances)


def test_job_criteria_system_prompt_requires_literal_grounded_evidence() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "evidence" in prompt
    assert "verbatim" in prompt
    assert "never paraphrase" in prompt
    assert "never be invented" in prompt


def test_user_prompt_preserves_description_and_excludes_metadata() -> None:
    description = "  Desenvolvedor Python\r\n\r\nRequisitos:\n- Python  "
    job = JobPosting(
        description=description,
        title="Backend Developer",
        company="Acme",
        location="Remote",
        source_url="internal-reference",
    )

    assert build_job_criteria_user_prompt(job) == description
