import re

from resume_ai.modules.candidate.application.import_schemas import (
    CandidateResumeExtraction,
    ExtractedCertification,
    ExtractedNamedItem,
    ExtractedProject,
    ResumeFieldEvidence,
)

TECHNOLOGIES = (
    "Python",
    "FastAPI",
    "Flutter",
    "PySide6",
    "PostgreSQL",
    "SQL Server",
    "SQL",
    "Next.js",
    "React",
    "SQLite",
    "APIs REST",
    "Banco de Dados Relacional",
    "Modelagem de Dados",
    "CRUD",
    "Programação Orientada a Objetos (POO)",
)
TOOLS = (
    "Git",
    "GitHub",
    "Linux",
    "Nmap",
    "pfSense",
    "FortiGate",
    "VMware",
    "Jira",
    "Nginx",
    "WordPress",
)
_COURSE_HEADINGS = {"CURSOS COMPLEMENTARES", "CURSOS", "CERTIFICAÇÕES", "CERTIFICATIONS"}
_KNOWN_PROVIDERS = {"udemy", "eurodata", "coursera", "alura", "senac", "aws", "microsoft"}


def _contains(line: str, value: str) -> bool:
    if value.casefold() in line.casefold():
        return True
    return bool(re.search(rf"(?<!\w){re.escape(value)}(?!\w)", line, re.IGNORECASE))


def _evidence(value: str, line: str) -> ResumeFieldEvidence:
    return ResumeFieldEvidence(value=value, evidence=line.strip())


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _add_named(
    existing: tuple[ExtractedNamedItem, ...],
    values: tuple[str, ...],
    lines: list[str],
) -> tuple[ExtractedNamedItem, ...]:
    result = list(existing)
    names = {item.name.value.casefold() for item in result}
    for value in values:
        line = next((line for line in lines if _contains(line, value)), None)
        if line is None:
            continue
        matching_index = next(
            (
                index
                for index, item in enumerate(result)
                if item.name.value.casefold() == value.casefold()
            ),
            None,
        )
        if matching_index is not None:
            item = result[matching_index]
            if " ".join(item.name.evidence.split()).casefold() not in " ".join(lines).casefold():
                result[matching_index] = item.model_copy(update={"name": _evidence(value, line)})
        else:
            result.append(ExtractedNamedItem(name=_evidence(value, line)))
            names.add(value.casefold())
    return tuple(result)


def _remove_reclassified(
    items: tuple[ExtractedNamedItem, ...], values: tuple[str, ...]
) -> tuple[ExtractedNamedItem, ...]:
    known = tuple(value.casefold() for value in values)
    return tuple(
        item
        for item in items
        if not any(item.name.value.casefold() == value for value in known)
    )


def _course_certifications(lines: list[str]) -> tuple[ExtractedCertification, ...]:
    try:
        start = (
            next(index for index, line in enumerate(lines) if line.upper() in _COURSE_HEADINGS)
            + 1
        )
    except StopIteration:
        return ()
    result: list[ExtractedCertification] = []
    for line in lines[start:]:
        if not line.startswith(("-", "•")) and re.fullmatch(r"[A-ZÁÉÍÓÚÇ0-9 /-]{4,}", line):
            break
        if not line.startswith(("-", "•")):
            continue
        text = line.lstrip("-• ").strip()
        parts = [part.strip() for part in re.split(r"\s+-\s+", text) if part.strip()]
        if not parts:
            continue
        provider_index = next(
            (
                index
                for index, part in enumerate(parts[1:], 1)
                if part.casefold() in _KNOWN_PROVIDERS
            ),
            1 if len(parts) > 1 else None,
        )
        issuer = _evidence(parts[provider_index], line) if provider_index is not None else None
        result.append(
            ExtractedCertification(
                name=_evidence(parts[0], line),
                issuer=issuer,
            )
        )
    return tuple(result)


def _merge_certifications(
    existing: tuple[ExtractedCertification, ...], additions: tuple[ExtractedCertification, ...]
) -> tuple[ExtractedCertification, ...]:
    result = list(existing)
    names = {item.name.value.casefold() for item in existing if item.name is not None}
    for item in additions:
        is_duplicate = item.name is not None and any(
            item.name.value.casefold() == name
            or item.name.value.casefold().startswith(f"{name} - ")
            or name.startswith(f"{item.name.value.casefold()} - ")
            for name in names
        )
        if item.name is not None and not is_duplicate:
            result.append(item)
            names.add(item.name.value.casefold())
    return tuple(result)


def _project_technologies(project: ExtractedProject, lines: list[str]) -> ExtractedProject:
    if project.name is None:
        return project
    try:
        start = next(
            index for index, line in enumerate(lines) if _contains(line, project.name.value)
        )
    except StopIteration:
        return project
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].upper().startswith("PROJETO:") or lines[index].upper() in {
            "COMPETÊNCIAS TÉCNICAS",
            "CURSOS COMPLEMENTARES",
        }:
            end = index
            break
    block = lines[start:end]
    result = list(project.technologies)
    names = {item.value.casefold() for item in result}
    for value in TECHNOLOGIES:
        line = next((line for line in block if _contains(line, value)), None)
        if line is not None and value.casefold() not in names:
            result.append(_evidence(value, line))
            names.add(value.casefold())
    return (
        project.model_copy(update={"technologies": tuple(result)})
        if len(result) != len(project.technologies)
        else project
    )


def enrich_extraction(
    resume_text: str, extraction: CandidateResumeExtraction
) -> CandidateResumeExtraction:
    lines = _lines(resume_text)
    technologies = _add_named(extraction.technologies, TECHNOLOGIES, lines)
    tools = _add_named(extraction.tools, TOOLS, lines)
    technologies = _remove_reclassified(technologies, TOOLS)
    skills = _remove_reclassified(extraction.skills, TECHNOLOGIES + TOOLS)
    certifications = _merge_certifications(extraction.certifications, _course_certifications(lines))
    projects = tuple(_project_technologies(project, lines) for project in extraction.projects)
    if (
        technologies == extraction.technologies
        and tools == extraction.tools
        and skills == extraction.skills
        and certifications == extraction.certifications
        and projects == extraction.projects
    ):
        return extraction
    return extraction.model_copy(
        update={
            "skills": skills,
            "technologies": technologies,
            "tools": tools,
            "certifications": certifications,
            "projects": projects,
        }
    )
