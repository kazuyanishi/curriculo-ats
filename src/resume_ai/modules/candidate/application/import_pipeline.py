from resume_ai.modules.candidate.application.grounding import CandidateResumeTruthGate
from resume_ai.modules.candidate.application.import_conversion import (
    CandidateResumeDraftConverter,
)
from resume_ai.modules.candidate.application.import_draft import (
    CandidateImportDraft,
    CandidateImportIssue,
)
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
        best_effort = getattr(self._truth_gate, "validate_best_effort", None)
        if best_effort is None:
            self._truth_gate.validate(resume_text, extraction)
            grounding_issues: tuple[CandidateImportIssue, ...] = ()
        else:
            extraction, grounding_issues = best_effort(resume_text, extraction)
        draft = self._converter.convert(extraction)
        if grounding_issues:
            return draft.model_copy(update={"issues": (*draft.issues, *grounding_issues)})
        return draft
