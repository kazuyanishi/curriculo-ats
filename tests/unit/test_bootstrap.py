import resume_ai
from resume_ai.main import main


def test_package_import_and_version() -> None:
    assert resume_ai.__version__ == "0.1.0"


def test_main_returns_success_and_prints_message(capsys) -> None:
    assert main() == 0
    assert capsys.readouterr().out == "Resume AI\n"
