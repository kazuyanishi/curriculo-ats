import pytest

from resume_ai.core.exceptions import DomainError
from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    Certification,
    ContactInfo,
    Education,
    EducationStatus,
    Experience,
    PersonalInfo,
    Skill,
    Technology,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    EducationRequirement,
    EducationRequirementStatus,
    ExperienceDurationUnit,
    ExperienceMinimumDuration,
    ExperienceRequirement,
    JobCriteria,
    JobCriterion,
)
from resume_ai.modules.matching.application.provenance import (
    MatchingProvenanceError,
    MatchingProvenanceGate,
)
from resume_ai.modules.matching.application.semantic_schemas import SemanticMatchBatch
from resume_ai.modules.matching.application.services import (
    CalculateMatchingScore,
    MatchAndScoreCandidateToJob,
    MatchCandidateToJob,
)
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.matching.domain.services import (
    DeterministicGapAnalyzer,
    ExactCandidateCriterionMatcher,
    MatchingScoreCalculator,
)
from resume_ai.modules.matching.infrastructure.semantic_refiner import AISemanticMatchingRefiner


def candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.test", "+55"),
        experiences=(
            Experience(
                "Example Systems",
                "Support Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(Activity("Organização e acompanhamento de chamados pelo Jira."),),
            ),
        ),
        education=(Education("Example University", "Computer Science", EducationStatus.COMPLETED),),
        skills=(Skill("Writing"), Skill("Planning"), Skill("Communication")),
        technologies=(Technology("PostgreSQL"), Technology("Python")),
        certifications=(
            Certification("Azure Fundamentals", "Microsoft"),
            Certification("AWS Certified Developer", "AWS"),
        ),
    )


def criterion(category: CriterionCategory, value: str, **kwargs) -> JobCriterion:
    return JobCriterion(category=category, value=value, evidence=value, **kwargs)


def test_criterion_match_rejects_invalid_path_collections() -> None:
    item = criterion(CriterionCategory.TECHNOLOGY, "Python")

    with pytest.raises(DomainError):
        CriterionMatch(item, MatchStatus.MATCHED, ["technologies[0].name"])  # type: ignore[arg-type]
    with pytest.raises(DomainError):
        CriterionMatch(item, MatchStatus.MATCHED, (" ",))
    with pytest.raises(DomainError):
        CriterionMatch(item, MatchStatus.MATCHED, ("technologies[0].name",) * 2)


def test_exact_name_matches_preserve_only_the_matched_path() -> None:
    matcher = ExactCandidateCriterionMatcher()
    subject = candidate()
    original = candidate()

    technology = matcher.match(subject, criterion(CriterionCategory.TECHNOLOGY, "Python"))
    skill = matcher.match(subject, criterion(CriterionCategory.SKILL, "Communication"))
    certification = matcher.match(
        subject, criterion(CriterionCategory.CERTIFICATION, "AWS Certified Developer")
    )

    assert technology.candidate_evidence_paths == ("technologies[1].name",)
    assert skill.candidate_evidence_paths == ("skills[2].name",)
    assert certification.candidate_evidence_paths == ("certifications[1].name",)
    assert subject == original


def test_education_match_preserves_only_required_fields() -> None:
    result = ExactCandidateCriterionMatcher().match(
        candidate(),
        criterion(
            CriterionCategory.EDUCATION,
            "Computer Science",
            education_requirement=EducationRequirement(
                field_of_study="Computer Science",
                acceptable_statuses=(EducationRequirementStatus.COMPLETED,),
            ),
        ),
    )

    assert result.status is MatchStatus.MATCHED
    assert result.candidate_evidence_paths == ("education[0].course", "education[0].status")


def test_experience_match_preserves_role_and_duration_fields() -> None:
    result = ExactCandidateCriterionMatcher().match(
        candidate(),
        criterion(
            CriterionCategory.EXPERIENCE,
            "Support Analyst for 3 years",
            experience_requirement=ExperienceRequirement(
                role="Support Analyst",
                minimum_duration=ExperienceMinimumDuration(3, ExperienceDurationUnit.YEARS),
                minimum_duration_evidence="3 years",
            ),
        ),
    )

    assert result.status is MatchStatus.MATCHED
    assert result.candidate_evidence_paths == (
        "experiences[0].role",
        "experiences[0].start_date",
        "experiences[0].end_date",
    )


class FakeSemanticClient:
    def __init__(self, batch: SemanticMatchBatch) -> None:
        self._batch = batch

    def generate(self, *, system_prompt, user_prompt, response_model):
        return self._batch


def test_semantic_match_preserves_only_grounded_matched_paths() -> None:
    original = MatchingResult(
        (
            CriterionMatch(
                criterion(CriterionCategory.OTHER, "Ticket management"), MatchStatus.NOT_MATCHED
            ),
            CriterionMatch(criterion(CriterionCategory.OTHER, "Missing"), MatchStatus.NOT_MATCHED),
            CriterionMatch(criterion(CriterionCategory.OTHER, "Unknown"), MatchStatus.UNSUPPORTED),
        )
    )
    batch = SemanticMatchBatch.model_validate(
        {
            "decisions": [
                {
                    "criterion_index": 0,
                    "status": "matched",
                    "evidence_paths": ["experiences[0].activities[0].description"],
                },
                {
                    "criterion_index": 1,
                    "status": "not_matched",
                    "evidence_paths": ["skills[2].name"],
                },
                {
                    "criterion_index": 2,
                    "status": "unsupported",
                    "evidence_paths": ["skills[2].name"],
                },
            ]
        }
    )

    result = AISemanticMatchingRefiner(FakeSemanticClient(batch)).refine(candidate(), original)

    assert result.matches[0].candidate_evidence_paths == (
        "experiences[0].activities[0].description",
    )
    assert result.matches[1].candidate_evidence_paths == ()
    assert result.matches[2].candidate_evidence_paths == ()


@pytest.mark.parametrize(
    "match",
    [
        CriterionMatch(criterion(CriterionCategory.TECHNOLOGY, "Python"), MatchStatus.MATCHED),
        CriterionMatch(
            criterion(CriterionCategory.TECHNOLOGY, "Python"),
            MatchStatus.NOT_MATCHED,
            ("technologies[1].name",),
        ),
        CriterionMatch(
            criterion(CriterionCategory.TECHNOLOGY, "Python"),
            MatchStatus.MATCHED,
            ("projects[77].description",),
        ),
    ],
)
def test_provenance_gate_rejects_invalid_final_matches(match: CriterionMatch) -> None:
    with pytest.raises(MatchingProvenanceError):
        MatchingProvenanceGate().validate(candidate(), MatchingResult((match,)))


def test_provenance_gate_accepts_exact_result_and_score_and_gaps_are_unchanged() -> None:
    subject = candidate()
    matcher = ExactCandidateCriterionMatcher()
    matched = matcher.match(subject, criterion(CriterionCategory.TECHNOLOGY, "Python"))
    result = MatchingResult(
        (
            matched,
            CriterionMatch(criterion(CriterionCategory.TOOL, "Docker"), MatchStatus.NOT_MATCHED),
            CriterionMatch(criterion(CriterionCategory.OTHER, "Unknown"), MatchStatus.UNSUPPORTED),
            matcher.match(subject, criterion(CriterionCategory.SKILL, "Communication")),
        )
    )

    MatchingProvenanceGate().validate(subject, result)
    score = CalculateMatchingScore(MatchingScoreCalculator()).execute(result)
    gaps = DeterministicGapAnalyzer().analyze(result)

    assert score.score == 2 / 3
    assert score.coverage == 3 / 4
    assert gaps.gaps == (result.matches[1],)
    assert gaps.unsupported == (result.matches[2],)


def test_provenance_gate_runs_before_score() -> None:
    invalid_result = MatchingResult(
        (CriterionMatch(criterion(CriterionCategory.TECHNOLOGY, "Python"), MatchStatus.MATCHED),)
    )

    class Matcher:
        def match(self, candidate, criteria):
            return invalid_result

    class Score:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, result):
            self.calls += 1
            raise AssertionError("score must not execute")

    score = Score()
    service = MatchAndScoreCandidateToJob(
        MatchCandidateToJob(Matcher(), MatchingProvenanceGate()), score
    )

    with pytest.raises(MatchingProvenanceError):
        service.execute(candidate(), JobCriteria((invalid_result.matches[0].criterion,)))

    assert score.calls == 0
