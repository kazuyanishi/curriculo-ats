from resume_ai.core.config import AppConfig
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.integrations.ai.openai_client import OpenAIStructuredAIClient
from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
from resume_ai.modules.candidate.application.import_conversion import (
    CandidateResumeDraftConverter,
)
from resume_ai.modules.candidate.application.import_pipeline import (
    ImportCandidateFromResumeText,
)
from resume_ai.modules.candidate.application.services import LoadCandidate
from resume_ai.modules.candidate.infrastructure.ai_candidate_extractor import (
    AIResumeCandidateExtractor,
)
from resume_ai.modules.candidate.infrastructure.json_repository import (
    JsonCandidateRepository,
)
from resume_ai.modules.documents.application.services import GenerateCandidateDocuments
from resume_ai.modules.documents.infrastructure.docx_renderer import DocxCandidateRenderer
from resume_ai.modules.documents.infrastructure.pdf_renderer import PdfCandidateRenderer
from resume_ai.modules.jobs.application.services import ExtractJobCriteria, LoadJob
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate
from resume_ai.modules.jobs.infrastructure.ai_extractor import AIJobCriteriaExtractor
from resume_ai.modules.jobs.infrastructure.text_repository import TextJobRepository
from resume_ai.modules.matching.application.matchers import (
    DeterministicCandidateJobMatcher,
    HybridCandidateJobMatcher,
)
from resume_ai.modules.matching.application.provenance import MatchingProvenanceGate
from resume_ai.modules.matching.application.services import (
    AnalyzeMatchingGaps,
    CalculateMatchingScore,
    MatchAndScoreCandidateToJob,
    MatchCandidateToJob,
)
from resume_ai.modules.matching.domain.services import (
    DeterministicGapAnalyzer,
    ExactCandidateCriterionMatcher,
    MatchingScoreCalculator,
)
from resume_ai.modules.matching.infrastructure.semantic_refiner import (
    AISemanticMatchingRefiner,
)
from resume_ai.modules.optimization.application.planning import BuildCandidateOptimizationPlan
from resume_ai.modules.optimization.application.services import (
    AnalyzeCandidateForJob,
    DeterministicCandidateOptimizationProposalApplier,
    GroundedCandidateOptimizer,
    OptimizeCandidate,
)
from resume_ai.modules.optimization.domain.services import DeterministicCandidateOptimizer
from resume_ai.modules.optimization.infrastructure.contextual_experience_optimizer import (
    AIContextualExperienceOptimizer,
)
from resume_ai.modules.optimization.infrastructure.semantic_optimization_truth_gate import (
    AISemanticOptimizationTruthGate,
)


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


def build_import_candidate_from_resume_text(
    config: AIConfig,
) -> ImportCandidateFromResumeText:
    client = OpenAIStructuredAIClient(config)
    extractor = AIResumeCandidateExtractor(client)
    return ImportCandidateFromResumeText(
        extractor=extractor,
        truth_gate=CandidateResumeTruthGate(),
        converter=CandidateResumeDraftConverter(),
    )


def build_match_candidate_to_job() -> MatchCandidateToJob:
    criterion_matcher = ExactCandidateCriterionMatcher()
    matcher = DeterministicCandidateJobMatcher(criterion_matcher)
    return MatchCandidateToJob(matcher, MatchingProvenanceGate())


def build_hybrid_match_candidate_to_job(config: AIConfig) -> MatchCandidateToJob:
    deterministic_matcher = DeterministicCandidateJobMatcher(ExactCandidateCriterionMatcher())
    semantic_refiner = AISemanticMatchingRefiner(OpenAIStructuredAIClient(config))
    return MatchCandidateToJob(
        HybridCandidateJobMatcher(deterministic_matcher, semantic_refiner),
        MatchingProvenanceGate(),
    )


def build_calculate_matching_score() -> CalculateMatchingScore:
    calculator = MatchingScoreCalculator()
    return CalculateMatchingScore(calculator)


def build_analyze_matching_gaps() -> AnalyzeMatchingGaps:
    analyzer = DeterministicGapAnalyzer()
    return AnalyzeMatchingGaps(analyzer)


def build_optimize_candidate() -> OptimizeCandidate:
    return OptimizeCandidate(DeterministicCandidateOptimizer())


def build_grounded_optimize_candidate(config: AIConfig) -> OptimizeCandidate:
    client = OpenAIStructuredAIClient(config)
    truth_gate = AISemanticOptimizationTruthGate(client)
    experience_optimizer = AIContextualExperienceOptimizer(client, truth_gate)
    grounded_optimizer = GroundedCandidateOptimizer(
        planner=BuildCandidateOptimizationPlan(MatchingProvenanceGate()),
        experience_optimizer=experience_optimizer,
        proposal_applier=DeterministicCandidateOptimizationProposalApplier(),
        deterministic_optimizer=DeterministicCandidateOptimizer(),
    )
    return OptimizeCandidate(grounded_optimizer)


def build_analyze_candidate_for_job(config: AIConfig) -> AnalyzeCandidateForJob:
    return AnalyzeCandidateForJob(
        criteria_extractor=build_extract_job_criteria(config),
        matcher=MatchAndScoreCandidateToJob(
            build_hybrid_match_candidate_to_job(config),
            build_calculate_matching_score(),
        ),
        gap_analyzer=build_analyze_matching_gaps(),
        optimizer=build_grounded_optimize_candidate(config),
    )


def build_generate_candidate_documents() -> GenerateCandidateDocuments:
    return GenerateCandidateDocuments(
        docx_renderer=DocxCandidateRenderer(),
        pdf_renderer=PdfCandidateRenderer(),
    )


def build_match_and_score_candidate_to_job() -> MatchAndScoreCandidateToJob:
    matcher = build_match_candidate_to_job()
    score_calculator = build_calculate_matching_score()
    return MatchAndScoreCandidateToJob(matcher, score_calculator)
