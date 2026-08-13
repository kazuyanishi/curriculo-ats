from typing import get_type_hints

import pytest

from resume_ai.modules.candidate.application.exceptions import ResumeCandidateGroundingError
from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
from resume_ai.modules.candidate.application.import_conversion import (
    CandidateResumeDraftConverter,
)
from resume_ai.modules.candidate.application.import_draft import (
    CandidateImportDraft,
    CandidateImportIssue,
    CandidateImportIssueCode,
)
from resume_ai.modules.candidate.application.import_pipeline import (
    ImportCandidateFromResumeText,
)
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction


class RecordingExtractor:
    def __init__(self, extraction=None, events=None, error=None) -> None:
        self.extraction = extraction or CandidateResumeExtraction()
        self.events = events if events is not None else []
        self.error = error
        self.received_text = None

    def extract(self, resume_text: str) -> CandidateResumeExtraction:
        self.events.append("extract")
        self.received_text = resume_text
        if self.error is not None:
            raise self.error
        return self.extraction


class RecordingGate:
    def __init__(self, events, error=None) -> None:
        self.events = events
        self.error = error
        self.received_text = None
        self.received_extraction = None

    def validate(self, resume_text: str, extraction: CandidateResumeExtraction) -> None:
        self.events.append("ground")
        self.received_text = resume_text
        self.received_extraction = extraction
        if self.error is not None:
            raise self.error


class RecordingConverter:
    def __init__(self, events, draft=None, error=None) -> None:
        self.events = events
        self.draft = draft or CandidateImportDraft()
        self.error = error
        self.received_extraction = None

    def convert(self, extraction: CandidateResumeExtraction) -> CandidateImportDraft:
        self.events.append("convert")
        self.received_extraction = extraction
        if self.error is not None:
            raise self.error
        return self.draft


def make_pipeline(extractor, gate, converter) -> ImportCandidateFromResumeText:
    return ImportCandidateFromResumeText(extractor, gate, converter)


def test_pipeline_executes_extract_ground_convert_in_order() -> None:
    events = []
    extractor = RecordingExtractor(events=events)
    gate = RecordingGate(events)
    converter = RecordingConverter(events)

    result = make_pipeline(extractor, gate, converter).execute("resume")

    assert events == ["extract", "ground", "convert"]
    assert isinstance(result, CandidateImportDraft)


def test_pipeline_preserves_same_text_and_extraction_identity() -> None:
    events = []
    extraction = CandidateResumeExtraction()
    extractor = RecordingExtractor(extraction=extraction, events=events)
    gate = RecordingGate(events)
    converter = RecordingConverter(events)
    text = "  Jane Doe\nPython   FastAPI\n  "

    make_pipeline(extractor, gate, converter).execute(text)

    assert extractor.received_text == text
    assert gate.received_text == text
    assert gate.received_extraction is extraction
    assert converter.received_extraction is extraction


def test_pipeline_returns_converter_draft_by_identity() -> None:
    events = []
    draft = CandidateImportDraft()
    converter = RecordingConverter(events, draft=draft)

    result = make_pipeline(
        RecordingExtractor(events=events), RecordingGate(events), converter
    ).execute("resume")

    assert result is draft


def test_extractor_failure_stops_gate_and_converter() -> None:
    events = []
    extractor = RecordingExtractor(events=events, error=RuntimeError("extract failure"))
    gate = RecordingGate(events)
    converter = RecordingConverter(events)

    with pytest.raises(RuntimeError, match="extract failure"):
        make_pipeline(extractor, gate, converter).execute("resume")

    assert events == ["extract"]


def test_truth_gate_failure_stops_converter_and_preserves_exception() -> None:
    events = []
    extraction = CandidateResumeExtraction()
    error = ResumeCandidateGroundingError("grounding failure")
    extractor = RecordingExtractor(extraction=extraction, events=events)
    gate = RecordingGate(events, error=error)
    converter = RecordingConverter(events)

    with pytest.raises(ResumeCandidateGroundingError) as raised:
        make_pipeline(extractor, gate, converter).execute("resume")

    assert raised.value is error
    assert events == ["extract", "ground"]


def test_converter_failure_is_propagated() -> None:
    events = []
    error = RuntimeError("conversion failure")
    converter = RecordingConverter(events, error=error)

    with pytest.raises(RuntimeError) as raised:
        make_pipeline(RecordingExtractor(events=events), RecordingGate(events), converter).execute(
            "resume"
        )

    assert raised.value is error
    assert events == ["extract", "ground", "convert"]


def test_draft_with_issues_is_a_valid_pipeline_result() -> None:
    events = []
    draft = CandidateImportDraft(
        issues=(
            CandidateImportIssue(
                path="personal_info.city",
                code=CandidateImportIssueCode.MISSING_REQUIRED_FIELD,
            ),
        )
    )
    converter = RecordingConverter(events, draft=draft)

    result = make_pipeline(
        RecordingExtractor(events=events), RecordingGate(events), converter
    ).execute("resume")

    assert result is draft
    assert result.issues[0].code == CandidateImportIssueCode.MISSING_REQUIRED_FIELD


def test_empty_extraction_integrates_real_gate_and_converter() -> None:
    extraction = CandidateResumeExtraction()
    extractor = RecordingExtractor(extraction=extraction)

    result = ImportCandidateFromResumeText(
        extractor,
        CandidateResumeTruthGate(),
        CandidateResumeDraftConverter(),
    ).execute("")

    assert isinstance(result, CandidateImportDraft)
    assert len(result.issues) == 6


def test_execute_type_hints_are_explicit() -> None:
    hints = get_type_hints(ImportCandidateFromResumeText.execute)

    assert hints["resume_text"] is str
    assert hints["return"] is CandidateImportDraft
