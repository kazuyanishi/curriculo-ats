
from typing import get_type_hints

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    Certification,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
    Language,
    PersonalInfo,
    Project,
    Skill,
    Technology,
    Tool,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import (
    CriterionMatch,
    MatchingResult,
    MatchStatus,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer


def _candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.com", "+55"),
        experiences=(
            Experience("Example Corp", "Backend Developer", YearMonth("2020-01")),
        ),
        education=(Education("Example University", "Computer Science", EducationStatus.COMPLETED),),
        skills=(Skill("Leadership"), Skill("Python"), Skill("Communication")),
        technologies=(Technology("Python"), Technology("FastAPI")),
        tools=(Tool("Docker"), Tool("Git")),
        languages=(Language("English"), Language("Portuguese")),
        certifications=(Certification("AWS", "Amazon"), Certification("Docker", "Docker")),
        projects=(Project("API", "Backend project"),),
    )


def _match(category: CriterionCategory, value: str, status: MatchStatus) -> CriterionMatch:
    return CriterionMatch(
        JobCriterion(category=category, value=value, evidence=f"{value} required."),
        status,
    )


def test_optimizer_stably_prioritizes_only_matched_supported_collections() -> None:
    candidate = _candidate()
    result = MatchingResult(
        matches=(
            _match(CriterionCategory.SKILL, "Communication", MatchStatus.MATCHED),
            _match(CriterionCategory.TECHNOLOGY, "FastAPI", MatchStatus.MATCHED),
            _match(CriterionCategory.TOOL, "Docker", MatchStatus.MATCHED),
            _match(CriterionCategory.LANGUAGE, "Portuguese", MatchStatus.MATCHED),
            _match(CriterionCategory.CERTIFICATION, "AWS", MatchStatus.MATCHED),
            _match(CriterionCategory.SKILL, "Python", MatchStatus.NOT_MATCHED),
            _match(CriterionCategory.TOOL, "Git", MatchStatus.UNSUPPORTED),
        )
    )

    optimized = DeterministicCandidateOptimizer().optimize(candidate, result)

    assert [item.name for item in optimized.skills] == ["Communication", "Leadership", "Python"]
    assert [item.name for item in optimized.technologies] == ["FastAPI", "Python"]
    assert [item.name for item in optimized.tools] == ["Docker", "Git"]
    assert [item.name for item in optimized.languages] == ["Portuguese", "English"]
    assert [item.name for item in optimized.certifications] == ["AWS", "Docker"]


def test_optimizer_preserves_all_objects_and_non_optimizable_order() -> None:
    candidate = _candidate()
    optimized = DeterministicCandidateOptimizer().optimize(candidate, MatchingResult())

    assert optimized is not candidate
    assert optimized.personal_info is candidate.personal_info
    assert optimized.contact_info is candidate.contact_info
    assert optimized.professional_links is candidate.professional_links
    assert optimized.experiences is candidate.experiences
    assert optimized.education is candidate.education
    assert optimized.projects is candidate.projects
    assert all(a is b for a, b in zip(optimized.skills, candidate.skills, strict=True))
    assert all(a is b for a, b in zip(optimized.technologies, candidate.technologies, strict=True))
    assert all(a is b for a, b in zip(optimized.tools, candidate.tools, strict=True))
    assert all(a is b for a, b in zip(optimized.languages, candidate.languages, strict=True))
    assert all(
        a is b
        for a, b in zip(optimized.certifications, candidate.certifications, strict=True)
    )


def test_optimizer_does_not_add_gaps_or_duplicate_items() -> None:
    candidate = _candidate()
    result = MatchingResult(
        matches=(
            _match(CriterionCategory.SKILL, "Missing", MatchStatus.NOT_MATCHED),
            _match(CriterionCategory.SKILL, "Leadership", MatchStatus.MATCHED),
        )
    )

    optimized = DeterministicCandidateOptimizer().optimize(candidate, result)

    assert len(optimized.skills) == len(candidate.skills)
    assert [item.name for item in optimized.skills] == ["Leadership", "Python", "Communication"]


def test_optimizer_type_hints() -> None:
    hints = get_type_hints(DeterministicCandidateOptimizer.optimize)

    assert hints["candidate"] is Candidate
    assert hints["result"] is MatchingResult
    assert hints["return"] is Candidate
