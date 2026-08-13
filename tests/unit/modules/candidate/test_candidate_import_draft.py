import pytest
from pydantic import ValidationError

from resume_ai.modules.candidate.application.import_draft import (
    CandidateImportDraft,
    CandidateImportIssue,
    CandidateImportIssueCode,
)


def test_empty_draft_is_valid() -> None:
    draft = CandidateImportDraft()

    assert draft.personal_info.full_name is None
    assert draft.experiences == ()
    assert draft.issues == ()


def test_issue_contains_stable_code_and_optional_raw_value() -> None:
    issue = CandidateImportIssue(
        path="education[0].status",
        code=CandidateImportIssueCode.UNSUPPORTED_EDUCATION_STATUS,
        raw_value="Trancado",
    )

    assert issue.code.value == "unsupported_education_status"
    assert issue.raw_value == "Trancado"


def test_draft_models_are_frozen_and_forbid_extra_fields() -> None:
    draft = CandidateImportDraft()

    with pytest.raises(ValidationError):
        CandidateImportDraft(unexpected=True)

    with pytest.raises(ValidationError):
        draft.personal_info = draft.personal_info
