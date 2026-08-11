import inspect
from pathlib import Path
from typing import get_type_hints

import pytest

import resume_ai.interfaces.cli.extract_job_criteria as cli
from resume_ai.core.config import AppConfig
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.modules.jobs.domain.entities import (
    CriterionCategory,
    CriterionImportance,
    JobCriteria,
    JobCriterion,
    JobPosting,
)


def _configs(tmp_path: Path) -> tuple[AppConfig, AIConfig]:
    app_config = AppConfig(
        project_root=tmp_path,
        package_root=tmp_path / "src" / "resume_ai",
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "output",
        environment="test",
    )
    return app_config, AIConfig(api_key="test-key", model="test-model")


def test_run_executes_the_dependencies_in_order_and_returns_criteria(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    app_config, ai_config = _configs(tmp_path)
    job = JobPosting(description="Python is required.")
    criteria = JobCriteria()
    events: list[tuple[str, object]] = []

    class FakeLoadJob:
        def execute(self) -> JobPosting:
            events.append(("load_job", job))
            return job

    class FakeExtraction:
        def execute(self, received_job: JobPosting) -> JobCriteria:
            events.append(("extract", received_job))
            return criteria

    def fake_load_config() -> AppConfig:
        events.append(("load_config", app_config))
        return app_config

    def fake_load_ai_config() -> AIConfig:
        events.append(("load_ai_config", ai_config))
        return ai_config

    def fake_build_load_job(received_config: AppConfig) -> FakeLoadJob:
        events.append(("build_load_job", received_config))
        return FakeLoadJob()

    def fake_build_extract(received_config: AIConfig) -> FakeExtraction:
        events.append(("build_extract", received_config))
        return FakeExtraction()

    monkeypatch.setattr(cli, "load_config", fake_load_config)
    monkeypatch.setattr(cli, "load_ai_config", fake_load_ai_config)
    monkeypatch.setattr(
        cli,
        "build_load_job",
        fake_build_load_job,
    )
    monkeypatch.setattr(
        cli,
        "build_extract_job_criteria",
        fake_build_extract,
    )

    result = cli.run()

    assert result is criteria
    assert events == [
        ("load_config", app_config),
        ("load_ai_config", ai_config),
        ("build_load_job", app_config),
        ("load_job", job),
        ("build_extract", ai_config),
        ("extract", job),
    ]


def test_main_prints_criteria(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    criteria = JobCriteria(
        criteria=(
            JobCriterion(
                category=CriterionCategory.TECHNOLOGY,
                value="Python",
                evidence="Python is required.",
                importance=CriterionImportance.REQUIRED,
            ),
        )
    )
    monkeypatch.setattr(cli, "run", lambda: criteria)

    result = cli.main()

    output = capsys.readouterr().out
    assert result == 0
    assert "required" in output
    assert "technology" in output
    assert "Python" in output
    assert "Python is required." in output


def test_main_prints_message_when_criteria_is_empty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "run", JobCriteria)

    result = cli.main()

    assert result == 0
    assert capsys.readouterr().out == "No job criteria found.\n"


def test_run_propagates_dependency_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail() -> AppConfig:
        raise RuntimeError("AI failure")

    monkeypatch.setattr(cli, "load_config", fail)

    with pytest.raises(RuntimeError, match="AI failure"):
        cli.run()


def test_cli_type_hints() -> None:
    run_hints = get_type_hints(cli.run)
    main_hints = get_type_hints(cli.main)

    assert run_hints["return"] is JobCriteria
    assert main_hints["return"] is int
    assert inspect.signature(cli.run).parameters == {}
