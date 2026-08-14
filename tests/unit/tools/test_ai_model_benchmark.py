import json
from decimal import Decimal

import pytest

from resume_ai.integrations.ai.client import AIUsage, StructuredAIOutputError
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction
from resume_ai.modules.jobs.application.schemas import JobCriteriaInput
from resume_ai.modules.matching.application.semantic_schemas import SemanticMatchBatch
from resume_ai.tools.ai_model_benchmark import (
    BENCHMARK_CASES,
    AIStage,
    BenchmarkCase,
    BenchmarkConfig,
    BenchmarkFailureKind,
    BenchmarkLimitError,
    BenchmarkRunner,
    ModelPricing,
    estimate_cost,
    load_pricing_snapshot,
    main,
    write_results,
)


class FakeStructuredAIClient:
    def __init__(self, responses, observer, usage=None) -> None:
        self._responses = iter(responses)
        self._observer = observer
        self._usage = AIUsage(1000, 400, 200) if usage is None else usage
        self.calls = 0
        self.requests = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls += 1
        self.requests.append((system_prompt, user_prompt, response_model))
        self._observer.record("fake", self._usage)
        return next(self._responses)


def candidate_extraction(reordered: bool = False) -> CandidateResumeExtraction:
    activities = [
        {
            "value": "Atendimento e acompanhamento de chamados.",
            "evidence": "Atendimento e acompanhamento de chamados.",
        },
        {
            "value": "Organização de demandas no Jira.",
            "evidence": "Organização de demandas no Jira.",
        },
    ]
    technologies = [
        {"name": {"value": "Python", "evidence": "Python"}},
        {"name": {"value": "PostgreSQL", "evidence": "PostgreSQL"}},
    ]
    if reordered:
        activities.reverse()
        technologies.reverse()
    return CandidateResumeExtraction.model_validate(
        {
            "personal_info": {
                "full_name": {"value": "Jane Doe", "evidence": "Jane Doe"},
                "city": {"value": "Curitiba", "evidence": "Curitiba"},
                "state": {"value": "Paraná", "evidence": "Paraná"},
                "country": {"value": "Brasil", "evidence": "Brasil"},
            },
            "experiences": [
                {
                    "company": {"value": "Example Systems", "evidence": "Example Systems"},
                    "role": {"value": "Support Analyst", "evidence": "Support Analyst"},
                    "activities": activities,
                }
            ],
            "education": [
                {
                    "course": {
                        "value": "Análise e Desenvolvimento de Sistemas",
                        "evidence": "Análise e Desenvolvimento de Sistemas",
                    }
                }
            ],
            "technologies": technologies,
        }
    )


def job_criteria(count=6) -> JobCriteriaInput:
    evidence = (
        "Knowledge of infrastructure, networks and technical support.",
        "Experience with Jira ticket management.",
        "Knowledge of information security best practices.",
        "English proficiency.",
        "Provide technical support to internal users.",
        "Troubleshoot hardware and software issues.",
    )[:count]
    return JobCriteriaInput.model_validate(
        {"criteria": [{"category": "skill", "value": item, "evidence": item} for item in evidence]}
    )


def semantic_batch() -> SemanticMatchBatch:
    return SemanticMatchBatch.model_validate(
        {
            "decisions": [
                {
                    "criterion_index": 0,
                    "status": "matched",
                    "evidence_paths": ["experiences[0].activities[0].description"],
                },
                {
                    "criterion_index": 1,
                    "status": "matched",
                    "evidence_paths": ["experiences[0].activities[1].description"],
                },
                {"criterion_index": 2, "status": "not_matched"},
                {"criterion_index": 3, "status": "unsupported"},
            ]
        }
    )


def factory_with(responses, clients):
    response_iterator = iter(responses)

    def factory(model, observer):
        client = FakeStructuredAIClient((next(response_iterator),), observer)
        clients.append(client)
        return client

    return factory


def test_dry_run_makes_no_api_calls_and_prints_plan(capsys) -> None:
    calls = []

    assert main(["--models", "model-a"], client_factory=lambda *args: calls.append(args)) == 0

    output = capsys.readouterr().out
    assert "DRY RUN" in output
    assert "Planned API executions: 3" in output
    assert "No API calls were made." in output
    assert calls == []


def test_max_calls_aborts_before_any_client_is_created() -> None:
    calls = []

    with pytest.raises(BenchmarkLimitError):
        BenchmarkRunner().run(
            BenchmarkConfig(("a", "b", "c"), max_calls=5), lambda *args: calls.append(args)
        )

    assert calls == []


def test_controlled_execution_captures_usage_and_scores_all_stages() -> None:
    clients = []
    results = BenchmarkRunner().run(
        BenchmarkConfig(("model-a",), max_calls=3),
        factory_with((candidate_extraction(), job_criteria(), semantic_batch()), clients),
    )

    assert len(clients) == 3
    assert all(client.calls == 1 for client in clients)
    assert [result.stage for result in results] == list(AIStage)
    assert all(result.quality_score == 1.0 for result in results)
    assert all(result.input_tokens == 1000 for result in results)
    assert all(result.cached_input_tokens == 400 for result in results)
    assert all(result.output_tokens == 200 for result in results)


def test_cli_execute_uses_the_injected_fake_client(capsys) -> None:
    clients = []

    result = main(
        ["--execute", "--models", "model-a", "--max-calls", "3"],
        environ={"RESUME_AI_API_KEY": "test-key"},
        client_factory=factory_with(
            (candidate_extraction(), job_criteria(), semantic_batch()), clients
        ),
    )

    assert result == 0
    assert len(clients) == 3
    assert "BENCHMARK RESULT" in capsys.readouterr().out


def test_cost_estimation_uses_decimal_and_cached_rate() -> None:
    pricing = ModelPricing("model", Decimal("1.00"), Decimal("0.10"), Decimal("5.00"))

    assert estimate_cost(AIUsage(1_000_000, 0, 1_000_000), pricing) == Decimal("6.00")
    assert estimate_cost(AIUsage(1_000_000, 400_000, 0), pricing) == Decimal("0.64")
    assert estimate_cost(AIUsage(10, 0, 5), None) is None


def test_missing_structured_output_is_a_schema_hard_fail_with_usage() -> None:
    class StructuredOutputFailureClient:
        def __init__(self, observer) -> None:
            self._observer = observer

        def generate(self, *, system_prompt, user_prompt, response_model):
            self._observer.record("model-a", AIUsage(1000, 400, 200))
            raise StructuredAIOutputError("missing parsed output")

    result = BenchmarkRunner((BENCHMARK_CASES[0],)).run(
        BenchmarkConfig(("model-a",), max_calls=1),
        lambda model, observer: StructuredOutputFailureClient(observer),
    )[0]

    assert result.failure_kind is BenchmarkFailureKind.SCHEMA
    assert result.hard_fail is True
    assert result.quality_score is None
    assert result.input_tokens == 1000
    assert result.cached_input_tokens == 400
    assert result.output_tokens == 200


def test_pricing_snapshot_is_loaded_from_local_decimal_strings(tmp_path) -> None:
    path = tmp_path / "pricing.local.json"
    path.write_text(
        json.dumps(
            {
                "as_of": "2026-08-14",
                "models": {
                    "model-a": {
                        "input_per_million": "1.00",
                        "cached_input_per_million": "0.10",
                        "output_per_million": "5.00",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    snapshot = load_pricing_snapshot(path)

    assert snapshot.as_of == "2026-08-14"
    assert snapshot.pricing_for("model-a").output_per_million == Decimal("5.00")


def test_grounding_failure_is_a_hard_fail() -> None:
    invalid = CandidateResumeExtraction.model_validate(
        {"personal_info": {"full_name": {"value": "Jane Doe", "evidence": "Invented"}}}
    )
    result = BenchmarkRunner((BENCHMARK_CASES[0],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((invalid,), [])
    )[0]

    assert result.hard_fail is True
    assert result.failure_kind is BenchmarkFailureKind.GROUNDING
    assert result.quality_score is None


def test_job_recall_and_semantic_accuracy_are_measured() -> None:
    clients = []
    job_result = BenchmarkRunner((BENCHMARK_CASES[1],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((job_criteria(4),), clients)
    )[0]
    semantic_result = BenchmarkRunner((BENCHMARK_CASES[2],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((semantic_batch(),), clients)
    )[0]

    assert job_result.quality_score == 4 / 6
    assert semantic_result.quality_score == 1.0


def test_candidate_quality_ignores_technology_and_activity_order() -> None:
    result = BenchmarkRunner((BENCHMARK_CASES[0],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((candidate_extraction(True),), [])
    )[0]

    assert result.quality_score == 1.0


def test_semantic_duration_fixture_is_open_ended_and_unsupported() -> None:
    clients = []
    result = BenchmarkRunner((BENCHMARK_CASES[2],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((semantic_batch(),), clients)
    )[0]
    payload = json.loads(clients[0].requests[0][1])
    catalog = {item["path"]: item["text"] for item in payload["candidate_evidence_catalog"]}

    assert result.quality_score == 1.0
    assert (
        catalog["experiences[1].activities[0].description"] == "Managing datacenter infrastructure."
    )
    assert "experiences[1].end_date" not in catalog


def test_result_file_contains_only_metrics(tmp_path) -> None:
    results = BenchmarkRunner((BENCHMARK_CASES[0],)).run(
        BenchmarkConfig(("model-a",), max_calls=1), factory_with((candidate_extraction(),), [])
    )
    path = tmp_path / "results.local.json"

    write_results(path, results)

    content = path.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert payload["results"][0]["case_id"] == "synthetic_candidate_extraction"
    for secret in ("Jane Doe", "Example Systems", "Curitiba", "Knowledge of infrastructure"):
        assert secret not in content


def test_production_ai_config_is_not_changed_by_benchmark() -> None:
    config = BenchmarkConfig()

    assert config.models == ("gpt-5.4-mini", "gpt-5.6-luna", "gpt-5.6-terra")
    assert BenchmarkCase(AIStage.CANDIDATE_EXTRACTION, "case").stage is AIStage.CANDIDATE_EXTRACTION
