from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "resume_ai"


def test_main_boundaries_exist() -> None:
    for boundary in ("core", "modules", "integrations", "interfaces"):
        assert (PACKAGE_ROOT / boundary).is_dir()


def test_planned_modules_exist() -> None:
    for module in (
        "candidate",
        "jobs",
        "matching",
        "optimization",
        "translation",
        "documents",
    ):
        assert (PACKAGE_ROOT / "modules" / module).is_dir()
