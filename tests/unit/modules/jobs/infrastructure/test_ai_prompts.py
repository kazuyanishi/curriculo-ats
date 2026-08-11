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


def test_job_criteria_system_prompt_classifies_programming_languages_as_technology() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "programming languages" in prompt
    assert "python" in prompt
    assert "java" in prompt
    assert "javascript" in prompt
    assert "as technology" in prompt
    assert "not classify programming" in prompt


def test_job_criteria_system_prompt_defines_human_languages() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "human spoken or written languages" in prompt
    assert "english" in prompt
    assert "portuguese" in prompt
    assert "as language" in prompt


def test_job_criteria_system_prompt_distinguishes_tools_from_skills() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "tool means" in prompt
    assert "docker" in prompt
    assert "git" in prompt
    assert "skill means" in prompt
    assert "communication" in prompt
    assert "do not use skill merely" in prompt


def test_job_criteria_system_prompt_documents_education_structure() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    for field in (
        "education_requirement",
        "degree_level",
        "field_of_study",
        "institution",
        "acceptable_statuses",
        "status_evidence",
        "status",
        "evidence",
    ):
        assert field in prompt


def test_job_criteria_system_prompt_documents_allowed_education_statuses() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "completed" in prompt
    assert "in_progress" in prompt
    assert "only completed and in_progress" in prompt
    assert "status is not specified" in prompt


def test_job_criteria_system_prompt_requires_conservative_education_grounding() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "do not infer" in prompt
    assert "explicitly supported" in prompt
    assert "same literal" in prompt
    assert "related field" in prompt
    assert "use null" in prompt


def test_job_criteria_system_prompt_requires_status_evidence_association() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "status_evidence.status must be present in acceptable_statuses" in prompt
    assert "every" in prompt
    assert "distinct acceptable status produced" in prompt
    assert "corresponding" in prompt
    assert "status_evidence item" in prompt
    assert "status_evidence.evidence" in prompt
    assert "criterion evidence" in prompt
    assert "literally and verbatim" in prompt


def test_job_criteria_system_prompt_documents_empty_status_provenance() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "when status is not specified" in prompt
    assert "both acceptable_statuses and status_evidence as empty lists" in prompt
    assert "omit that" in prompt
    assert "instead of inventing evidence" in prompt


def test_job_criteria_system_prompt_documents_independent_status_evidence() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "graduat" in prompt
    assert "currently enrolled" in prompt
    assert "independent literal" in prompt
    assert "evidence for completed and in_progress" in prompt


def test_job_criteria_system_prompt_requires_null_for_non_education() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "other than education" in prompt
    assert "education_requirement must be null" in prompt


def test_job_criteria_system_prompt_rejects_empty_and_or_education_structures() -> None:
    prompt = JOB_CRITERIA_SYSTEM_PROMPT.lower()

    assert "do not create an empty education_requirement object" in prompt
    assert "education is an alternative to" in prompt
    assert "experience" in prompt
    assert "never turn education or experience into two mandatory criteria" in prompt


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
