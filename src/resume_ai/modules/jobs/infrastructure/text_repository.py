from pathlib import Path

from resume_ai.modules.jobs.domain.entities import JobPosting


class TextJobRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def get(self) -> JobPosting:
        with self._path.open("r", encoding="utf-8", newline="") as file:
            content = file.read()
        return JobPosting(description=content)
