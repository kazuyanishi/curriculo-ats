from dataclasses import dataclass
from datetime import date

from resume_ai.modules.candidate.domain.entities import Candidate


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    path: str
    text: str


def _add(entries: list[CandidateEvidence], path: str, value: object) -> None:
    if value is not None:
        entries.append(CandidateEvidence(path, str(value)))


def build_candidate_evidence_catalog(candidate: Candidate) -> tuple[CandidateEvidence, ...]:
    entries: list[CandidateEvidence] = []
    for name in ("city", "state", "country"):
        _add(entries, f"personal_info.{name}", getattr(candidate.personal_info, name))

    for index, experience in enumerate(candidate.experiences):
        prefix = f"experiences[{index}]"
        for name in ("company", "role", "start_date", "end_date"):
            _add(entries, f"{prefix}.{name}", getattr(experience, name))
        for collection_name in ("activities", "achievements"):
            for item_index, item in enumerate(getattr(experience, collection_name)):
                _add(
                    entries,
                    f"{prefix}.{collection_name}[{item_index}].description",
                    item.description,
                )

    for index, education in enumerate(candidate.education):
        prefix = f"education[{index}]"
        for name in ("institution", "course", "status", "start_date", "end_date"):
            _add(entries, f"{prefix}.{name}", getattr(education, name))

    for collection_name in ("skills", "technologies", "tools", "languages"):
        for index, item in enumerate(getattr(candidate, collection_name)):
            prefix = f"{collection_name}[{index}]"
            _add(entries, f"{prefix}.name", item.name)
            _add(entries, f"{prefix}.level", item.level)

    for index, certification in enumerate(candidate.certifications):
        prefix = f"certifications[{index}]"
        for name in (
            "name",
            "issuer",
            "issue_date",
            "expiration_date",
            "credential_id",
        ):
            value = getattr(certification, name)
            if isinstance(value, date):
                value = value.isoformat()
            _add(entries, f"{prefix}.{name}", value)

    for index, project in enumerate(candidate.projects):
        prefix = f"projects[{index}]"
        for name in ("name", "description", "start_date", "end_date"):
            _add(entries, f"{prefix}.{name}", getattr(project, name))
        for technology_index, technology in enumerate(project.technologies):
            _add(entries, f"{prefix}.technologies[{technology_index}]", technology)

    return tuple(entries)
