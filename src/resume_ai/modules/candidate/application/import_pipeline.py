from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
from resume_ai.modules.candidate.application.import_conversion import (
    CandidateResumeDraftConverter,
)
from resume_ai.modules.candidate.application.import_draft import CandidateImportDraft
from resume_ai.modules.candidate.application.import_schemas import CandidateResumeExtraction
from resume_ai.modules.candidate.application.ports import ResumeCandidateExtractor


class ImportCandidateFromResumeText:
    def __init__(
        self,
        extractor: ResumeCandidateExtractor,
        truth_gate: CandidateResumeTruthGate,
        converter: CandidateResumeDraftConverter,
    ) -> None:
        self._extractor = extractor
        self._truth_gate = truth_gate
        self._converter = converter

    def execute(self, resume_text: str) -> CandidateImportDraft:
        extraction: CandidateResumeExtraction = self._extractor.extract(resume_text)
        self._truth_gate.validate(resume_text, extraction)
        return self._converter.convert(extraction)
