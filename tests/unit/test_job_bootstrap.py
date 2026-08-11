from pathlib import Path
from typing import get_type_hints

import pytest

from resume_ai.bootstrap import build_load_job
from resume_ai.core.config import AppConfig
from resume_ai.modules.jobs.application.services import LoadJob


def _config(tmp_path: Path, data_dir: Path | None = None) -> AppConfig:
    return AppConfig(
        project_root=tmp_path,
        package_root=tmp_path / "src" / "resume_ai",
        data_dir=tmp_path / "data" if data_dir is None else data_dir,
        output_dir=tmp_path / "output",
        environment="test",
    )


def _write_job(data_dir: Path, content: str) -> None:
    path = data_dir / "jobs" / "job.txt"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")


def test_build_returns_load_job_without_reading_file(tmp_path: Path) -> None:
    service = build_load_job(_config(tmp_path))

    assert isinstance(service, LoadJob)

    with pytest.raises(FileNotFoundError):
        service.execute()


def test_build_uses_config_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "custom-data"
    _write_job(data_dir, "Example job A")

    job = build_load_job(_config(tmp_path, data_dir=data_dir)).execute()

    assert job.description == "Example job A"


def test_build_respects_different_configs(tmp_path: Path) -> None:
    data_dir_a = tmp_path / "data-a"
    data_dir_b = tmp_path / "data-b"
    _write_job(data_dir_a, "First job")
    _write_job(data_dir_b, "Second job")

    service_a = build_load_job(_config(tmp_path, data_dir=data_dir_a))
    service_b = build_load_job(_config(tmp_path, data_dir=data_dir_b))

    assert service_a.execute().description == "First job"
    assert service_b.execute().description == "Second job"


def test_build_load_job_type_hints() -> None:
    hints = get_type_hints(build_load_job)

    assert hints["config"] is AppConfig
    assert hints["return"] is LoadJob
