"""Safe local benchmark for the AI stages already used by Resume AI.

This module never runs as part of the application or pytest. Its CLI is dry-run
by default; callers must explicitly opt in with ``--execute``.
"""

import argparse
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from resume_ai.core.exceptions import DomainError
from resume_ai.integrations.ai.client import (
    AIUsage,
    AIUsageObserver,
    StructuredAIClient,
    StructuredAIOutputError,
)
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.integrations.ai.openai_client import OpenAIStructuredAIClient
from resume_ai.modules.candidate.application.exceptions import ResumeCandidateGroundingError
from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction
from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.candidate.infrastructure.ai_candidate_extractor import (
    AIResumeCandidateExtractor,
)
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriterion,
    JobPosting,
)
from resume_ai.modules.jobs.domain.services import JobCriteriaTruthGate
from resume_ai.modules.jobs.infrastructure.ai_extractor import AIJobCriteriaExtractor
from resume_ai.modules.matching.application.exceptions import SemanticMatchingGroundingError
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.matching.infrastructure.semantic_refiner import AISemanticMatchingRefiner

DEFAULT_MODELS = ("gpt-5.4-mini", "gpt-5.6-luna", "gpt-5.6-terra")

SYNTHETIC_RESUME_TEXT = """Jane Doe
Curitiba - Paraná - Brasil

EMPRESA: Example Systems
CARGO: Support Analyst
PERÍODO: 01/2024 - Atual
- Atendimento e acompanhamento de chamados.
- Organização de demandas no Jira.
- Configuração de redes e servidores.

Análise e Desenvolvimento de Sistemas
Example University
Em andamento

Tecnologias:
Python
PostgreSQL
"""

SYNTHETIC_JOB_TEXT = """Requirements:
- Knowledge of infrastructure, networks and technical support.
- Experience with Jira ticket management.
- Knowledge of information security best practices.
- English proficiency.

Responsibilities:
- Provide technical support to internal users.
- Troubleshoot hardware and software issues.
"""


class AIStage(StrEnum):
    CANDIDATE_EXTRACTION = "candidate_extraction"
    JOB_CRITERIA_EXTRACTION = "job_criteria_extraction"
    SEMANTIC_MATCHING = "semantic_matching"


class BenchmarkFailureKind(StrEnum):
    SCHEMA = "schema"
    GROUNDING = "grounding"
    API = "api"
    TIMEOUT = "timeout"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    models: tuple[str, ...] = DEFAULT_MODELS
    max_calls: int = 20

    def __post_init__(self) -> None:
        if not self.models or any(not model.strip() for model in self.models):
            raise ValueError("benchmark models must be non-blank")
        if self.max_calls < 1:
            raise ValueError("max_calls must be at least one")


@dataclass(frozen=True, slots=True)
class ModelPricing:
    model: str
    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal


@dataclass(frozen=True, slots=True)
class PricingSnapshot:
    as_of: str
    rates: tuple[ModelPricing, ...]

    def pricing_for(self, model: str) -> ModelPricing | None:
        return next((rate for rate in self.rates if rate.model == model), None)


@dataclass(frozen=True, slots=True)
class BenchmarkCaseResult:
    stage: AIStage
    case_id: str
    model: str
    passed: bool
    hard_fail: bool
    quality_score: float | None
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    latency_ms: float
    estimated_cost_usd: Decimal | None
    failure_kind: BenchmarkFailureKind | None = None


@dataclass(frozen=True, slots=True)
class ModelBenchmarkSummary:
    model: str
    cases: tuple[BenchmarkCaseResult, ...]
    hard_fail_count: int
    average_quality_score: float | None
    total_input_tokens: int
    total_cached_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: Decimal | None
    average_latency_ms: float


class BenchmarkLimitError(Exception):
    pass


class UsageCollector(AIUsageObserver):
    def __init__(self) -> None:
        self.usage = AIUsage()

    def record(self, model: str, usage: AIUsage) -> None:
        self.usage = usage


ClientFactory = Callable[[str, AIUsageObserver], StructuredAIClient]


def _candidate_fact_score(extraction: CandidateResumeExtraction) -> float:
    experience = next(
        (
            item
            for item in extraction.experiences
            if item.company is not None
            and item.company.value == "Example Systems"
            and item.role is not None
            and item.role.value == "Support Analyst"
        ),
        None,
    )
    facts = (
        extraction.personal_info.full_name is not None
        and extraction.personal_info.full_name.value == "Jane Doe",
        extraction.personal_info.city is not None
        and extraction.personal_info.city.value == "Curitiba",
        extraction.personal_info.state is not None
        and extraction.personal_info.state.value == "Paraná",
        extraction.personal_info.country is not None
        and extraction.personal_info.country.value == "Brasil",
        any(
            item.company is not None and item.company.value == "Example Systems"
            for item in extraction.experiences
        ),
        any(
            item.company is not None
            and item.company.value == "Example Systems"
            and item.role is not None
            and item.role.value == "Support Analyst"
            for item in extraction.experiences
        ),
        experience is not None
        and any(
            activity.value == "Organização de demandas no Jira."
            for activity in experience.activities
        ),
        any(
            education.course is not None
            and education.course.value == "Análise e Desenvolvimento de Sistemas"
            for education in extraction.education
        ),
        any(technology.name.value == "Python" for technology in extraction.technologies),
    )
    return sum(facts) / len(facts)


def _synthetic_semantic_candidate() -> Candidate:
    return Candidate(
        personal_info=PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        contact_info=ContactInfo("jane@example.test", "+55 41 99999-0000"),
        experiences=(
            Experience(
                "Example Systems",
                "Support Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(
                    Activity("Organização e acompanhamento de chamados pelo Jira."),
                    Activity("Configuração de redes e servidores."),
                    Activity("Troubleshooting de hardware e software."),
                ),
            ),
            Experience(
                "Example Systems",
                "Infrastructure Analyst",
                YearMonth("2024-01"),
                None,
                activities=(Activity("Managing datacenter infrastructure."),),
            ),
        ),
    )


def _synthetic_semantic_result() -> MatchingResult:
    values = (
        "Experience with ticket management",
        "Knowledge of infrastructure and networks",
        "Kubernetes administration",
        "At least five years managing datacenter infrastructure",
    )
    return MatchingResult(
        tuple(
            CriterionMatch(
                JobCriterion(CriterionCategory.OTHER, value, value, CriterionImportance.REQUIRED),
                MatchStatus.NOT_MATCHED,
            )
            for value in values
        )
    )


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    stage: AIStage
    case_id: str

    def run(self, client: StructuredAIClient) -> float:
        if self.stage is AIStage.CANDIDATE_EXTRACTION:
            extraction = AIResumeCandidateExtractor(client).extract(SYNTHETIC_RESUME_TEXT)
            CandidateResumeTruthGate().validate(SYNTHETIC_RESUME_TEXT, extraction)
            return _candidate_fact_score(extraction)
        if self.stage is AIStage.JOB_CRITERIA_EXTRACTION:
            job = JobPosting(SYNTHETIC_JOB_TEXT)
            criteria = AIJobCriteriaExtractor(client).extract(job)
            JobCriteriaTruthGate().validate(job, criteria)
            expected = (
                "Knowledge of infrastructure, networks and technical support.",
                "Experience with Jira ticket management.",
                "Knowledge of information security best practices.",
                "English proficiency.",
                "Provide technical support to internal users.",
                "Troubleshoot hardware and software issues.",
            )
            return sum(
                any(evidence in item.evidence for item in criteria.criteria)
                for evidence in expected
            ) / len(expected)
        result = AISemanticMatchingRefiner(client).refine(
            _synthetic_semantic_candidate(), _synthetic_semantic_result()
        )
        expected_statuses = (
            MatchStatus.MATCHED,
            MatchStatus.MATCHED,
            MatchStatus.NOT_MATCHED,
            MatchStatus.UNSUPPORTED,
        )
        return sum(
            match.status is status
            for match, status in zip(result.matches, expected_statuses, strict=True)
        ) / len(expected_statuses)


BENCHMARK_CASES = (
    BenchmarkCase(AIStage.CANDIDATE_EXTRACTION, "synthetic_candidate_extraction"),
    BenchmarkCase(AIStage.JOB_CRITERIA_EXTRACTION, "synthetic_job_criteria"),
    BenchmarkCase(AIStage.SEMANTIC_MATCHING, "synthetic_semantic_matching"),
)


def load_pricing_snapshot(path: Path) -> PricingSnapshot:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rates = tuple(
        ModelPricing(
            model=model,
            input_per_million=Decimal(values["input_per_million"]),
            cached_input_per_million=Decimal(values["cached_input_per_million"]),
            output_per_million=Decimal(values["output_per_million"]),
        )
        for model, values in raw["models"].items()
    )
    return PricingSnapshot(as_of=raw["as_of"], rates=rates)


def estimate_cost(usage: AIUsage, pricing: ModelPricing | None) -> Decimal | None:
    if pricing is None or usage.input_tokens is None or usage.output_tokens is None:
        return None
    cached = usage.cached_input_tokens or 0
    uncached = usage.input_tokens - cached
    if uncached < 0:
        return None
    million = Decimal("1000000")
    return (
        Decimal(uncached) * pricing.input_per_million
        + Decimal(cached) * pricing.cached_input_per_million
        + Decimal(usage.output_tokens) * pricing.output_per_million
    ) / million


def _failure(error: Exception) -> tuple[BenchmarkFailureKind, bool]:
    if isinstance(
        error, (ResumeCandidateGroundingError, SemanticMatchingGroundingError, DomainError)
    ):
        return BenchmarkFailureKind.GROUNDING, True
    if isinstance(error, (ValidationError, StructuredAIOutputError)):
        return BenchmarkFailureKind.SCHEMA, True
    if isinstance(error, TimeoutError):
        return BenchmarkFailureKind.TIMEOUT, False
    if error.__class__.__module__.startswith("openai"):
        return BenchmarkFailureKind.API, False
    return BenchmarkFailureKind.OTHER, False


class BenchmarkRunner:
    def __init__(self, cases: Sequence[BenchmarkCase] = BENCHMARK_CASES) -> None:
        self._cases = tuple(cases)

    def planned_calls(self, config: BenchmarkConfig) -> int:
        return len(config.models) * len(self._cases)

    def run(
        self,
        config: BenchmarkConfig,
        client_factory: ClientFactory,
        pricing: PricingSnapshot | None = None,
    ) -> tuple[BenchmarkCaseResult, ...]:
        planned = self.planned_calls(config)
        if planned > config.max_calls:
            raise BenchmarkLimitError(
                f"Planned benchmark requires {planned} API calls, which exceeds "
                f"--max-calls {config.max_calls}."
            )
        results: list[BenchmarkCaseResult] = []
        for model in config.models:
            for case in self._cases:
                collector = UsageCollector()
                started = time.perf_counter()
                try:
                    quality_score = case.run(client_factory(model, collector))
                    failure_kind = None
                    hard_fail = False
                except Exception as error:
                    quality_score = None
                    failure_kind, hard_fail = _failure(error)
                latency_ms = (time.perf_counter() - started) * 1000
                usage = collector.usage
                results.append(
                    BenchmarkCaseResult(
                        stage=case.stage,
                        case_id=case.case_id,
                        model=model,
                        passed=failure_kind is None,
                        hard_fail=hard_fail,
                        quality_score=quality_score,
                        input_tokens=usage.input_tokens,
                        cached_input_tokens=usage.cached_input_tokens,
                        output_tokens=usage.output_tokens,
                        latency_ms=latency_ms,
                        estimated_cost_usd=estimate_cost(
                            usage, None if pricing is None else pricing.pricing_for(model)
                        ),
                        failure_kind=failure_kind,
                    )
                )
        return tuple(results)


def summarize(results: Sequence[BenchmarkCaseResult]) -> tuple[ModelBenchmarkSummary, ...]:
    summaries: list[ModelBenchmarkSummary] = []
    for model in dict.fromkeys(result.model for result in results):
        cases = tuple(result for result in results if result.model == model)
        qualities = [result.quality_score for result in cases if result.quality_score is not None]
        costs = [
            result.estimated_cost_usd for result in cases if result.estimated_cost_usd is not None
        ]
        summaries.append(
            ModelBenchmarkSummary(
                model=model,
                cases=cases,
                hard_fail_count=sum(result.hard_fail for result in cases),
                average_quality_score=None if not qualities else sum(qualities) / len(qualities),
                total_input_tokens=sum(result.input_tokens or 0 for result in cases),
                total_cached_input_tokens=sum(result.cached_input_tokens or 0 for result in cases),
                total_output_tokens=sum(result.output_tokens or 0 for result in cases),
                total_estimated_cost_usd=None if not costs else sum(costs, Decimal()),
                average_latency_ms=sum(result.latency_ms for result in cases) / len(cases),
            )
        )
    return tuple(summaries)


def write_results(path: Path, results: Sequence[BenchmarkCaseResult]) -> None:
    payload = {
        "results": [
            {
                **asdict(result),
                "stage": result.stage.value,
                "failure_kind": None if result.failure_kind is None else result.failure_kind.value,
                "estimated_cost_usd": (
                    None if result.estimated_cost_usd is None else str(result.estimated_cost_usd)
                ),
            }
            for result in results
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_summaries(results: Sequence[BenchmarkCaseResult]) -> None:
    print("BENCHMARK RESULT")
    print("MODEL | QUALITY | HARD FAILS | INPUT TOKENS | OUTPUT TOKENS | AVG LATENCY | EST. COST")
    for summary in summarize(results):
        quality = (
            "N/A"
            if summary.average_quality_score is None
            else f"{summary.average_quality_score:.2f}"
        )
        cost = (
            "N/A"
            if summary.total_estimated_cost_usd is None
            else f"${summary.total_estimated_cost_usd}"
        )
        print(
            f"{summary.model} | {quality} | {summary.hard_fail_count} | "
            f"{summary.total_input_tokens} | {summary.total_output_tokens} | "
            f"{summary.average_latency_ms:.0f}ms | {cost}"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark local e seguro de modelos de IA")
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--pricing", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-calls", type=int, default=20)
    parser.add_argument("--execute", action="store_true")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    client_factory: ClientFactory | None = None,
) -> int:
    args = _parser().parse_args(argv)
    config = BenchmarkConfig(models=tuple(args.models), max_calls=args.max_calls)
    runner = BenchmarkRunner()
    planned = runner.planned_calls(config)
    stage_calls = len(config.models)
    if not args.execute:
        print("DRY RUN")
        print(f"Models: {len(config.models)}")
        print(f"Cases: {len(BENCHMARK_CASES)}")
        print(f"Candidate extraction calls: {stage_calls}")
        print(f"Job criteria calls: {stage_calls}")
        print(f"Semantic matching calls: {stage_calls}")
        print(f"Planned API executions: {planned}")
        print("No API calls were made.")
        return 0
    if planned > config.max_calls:
        print(
            f"Planned benchmark requires {planned} API calls, which exceeds "
            f"--max-calls {config.max_calls}."
        )
        return 2
    source = os.environ if environ is None else environ
    api_key = source.get("RESUME_AI_API_KEY", "").strip()
    if not api_key:
        print("RESUME_AI_API_KEY is required when --execute is used.")
        return 2
    pricing = None if args.pricing is None else load_pricing_snapshot(args.pricing)
    factory = client_factory
    if factory is None:

        def factory(model: str, observer: AIUsageObserver) -> StructuredAIClient:
            return OpenAIStructuredAIClient(AIConfig(api_key=api_key, model=model), observer)

    results = runner.run(config, factory, pricing)
    if args.output is not None:
        write_results(args.output, results)
    _print_summaries(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
