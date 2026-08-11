from pathlib import Path
from typing import get_type_hints

import pytest

from resume_ai.bootstrap import build_load_candidate
from resume_ai.core.config import AppConfig
from resume_ai.modules.candidate.application.services import LoadCandidate


def _config(tmp_path: Path, data_dir: Path | None = None) -> AppConfig:
    return AppConfig(
        project_root=tmp_path,
        package_root=tmp_path / "src" / "resume_ai",
        data_dir=tmp_path / "data" if data_dir is None else data_dir,
        output_dir=tmp_path / "output",
        environment="test",
    )


def _minimum_json(name: str) -> str:
    return f"""
    {{
      "personal_info": {{
        "full_name": "{name}",
        "city": "Curitiba",
        "state": "PR",
        "country": "Brazil"
      }},
      "contact_info": {{
        "email": "jane@example.com",
        "phone": "+55 41 99999-0000"
      }}
    }}
    """


def _write_master(data_dir: Path, name: str) -> None:
    path = data_dir / "candidate" / "resume_master.json"
    path.parent.mkdir(parents=True)
    path.write_text(_minimum_json(name), encoding="utf-8")


def test_build_returns_load_candidate_without_reading_file(tmp_path: Path) -> None:
    service = build_load_candidate(_config(tmp_path))

    assert isinstance(service, LoadCandidate)

    with pytest.raises(FileNotFoundError):
        service.execute()


def test_build_uses_config_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "custom-data"
    _write_master(data_dir, "Jane Doe")

    service = build_load_candidate(_config(tmp_path, data_dir=data_dir))

    assert service.execute().personal_info.full_name == "Jane Doe"


def test_build_respects_different_configs(tmp_path: Path) -> None:
    data_dir_a = tmp_path / "data-a"
    data_dir_b = tmp_path / "data-b"
    _write_master(data_dir_a, "Jane Doe")
    _write_master(data_dir_b, "John Doe")

    service_a = build_load_candidate(_config(tmp_path, data_dir=data_dir_a))
    service_b = build_load_candidate(_config(tmp_path, data_dir=data_dir_b))

    assert service_a.execute().personal_info.full_name == "Jane Doe"
    assert service_b.execute().personal_info.full_name == "John Doe"


def test_build_type_hints() -> None:
    hints = get_type_hints(build_load_candidate)

    assert hints["config"] is AppConfig
    assert hints["return"] is LoadCandidate
