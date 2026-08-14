import logging
from dataclasses import fields, is_dataclass
from enum import StrEnum
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile

from resume_ai.bootstrap import (
    build_analyze_candidate_for_job,
    build_generate_candidate_documents,
    build_import_candidate_from_resume_text,
)
from resume_ai.core.exceptions import DomainError
from resume_ai.integrations.ai.config import load_ai_config
from resume_ai.interfaces.api.schemas import AnalyzeRequest, AnalyzeResponse
from resume_ai.modules.candidate.application.exceptions import (
    ResumeCandidateGroundingError,
    ResumeTextExtractionError,
)
from resume_ai.modules.candidate.application.import_draft import CandidateImportDraft
from resume_ai.modules.candidate.application.schemas import CandidateInput
from resume_ai.modules.candidate.domain.entities import Candidate
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.candidate.infrastructure.docx_text_extractor import (
    DocxResumeTextExtractor,
)
from resume_ai.modules.candidate.infrastructure.pdf_text_extractor import (
    PdfResumeTextExtractor,
)
from resume_ai.modules.jobs.domain.entities import JobPosting
from resume_ai.modules.optimization.application.services import CandidateAnalysisResult

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_RESUME_FILE_BYTES = 5 * 1024 * 1024


def _json_value(value: Any) -> Any:
    if isinstance(value, YearMonth):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _analysis_response(result: CandidateAnalysisResult) -> AnalyzeResponse:
    def match_response(item: object) -> dict[str, Any]:
        value = _json_value(item)
        return {"criterion": value["criterion"], "status": value["status"]}

    return AnalyzeResponse(
        criteria=[_json_value(item) for item in result.criteria.criteria],
        matching=[match_response(item) for item in result.matching.matches],
        score=_json_value(result.score),
        gaps={
            "gaps": [match_response(item) for item in result.gaps.gaps],
            "unsupported": [match_response(item) for item in result.gaps.unsupported],
        },
        optimized_candidate=_json_value(result.optimized_candidate),
    )


def _candidate_from_request(request: AnalyzeRequest) -> tuple[Candidate, JobPosting]:
    return request.candidate.to_domain(), request.job.to_domain()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/candidate/import", response_model=CandidateImportDraft)
async def import_candidate_resume(
    http_request: Request,
    file: Annotated[UploadFile, File(...)],
) -> CandidateImportDraft:
    try:
        filename = file.filename or ""
        suffix = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
        if suffix not in {"pdf", "docx"}:
            raise HTTPException(status_code=415, detail="Unsupported resume file type")

        content = await file.read(MAX_RESUME_FILE_BYTES + 1)
        if len(content) > MAX_RESUME_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Resume file is too large")
        if not content:
            raise HTTPException(status_code=422, detail="Resume file is empty")

        text_extractor = PdfResumeTextExtractor() if suffix == "pdf" else DocxResumeTextExtractor()
        try:
            resume_text = text_extractor.extract(content)
        except ResumeTextExtractionError as error:
            raise HTTPException(
                status_code=422, detail="Could not extract text from resume"
            ) from error

        if not resume_text.strip():
            raise HTTPException(status_code=422, detail="Resume contains no extractable text")

        ai_config = http_request.app.state.ai_config
        if ai_config is None:
            try:
                ai_config = load_ai_config()
            except ValueError as error:
                raise HTTPException(
                    status_code=503, detail="AI configuration unavailable"
                ) from error

        try:
            return build_import_candidate_from_resume_text(ai_config).execute(resume_text)
        except ResumeCandidateGroundingError as error:
            logger.warning(
                "Candidate resume grounding failed path=%s reason=%s "
                "whitespace_normalized_match=%s",
                error.path,
                error.reason,
                str(error.whitespace_normalized_match).lower(),
            )
            raise HTTPException(
                status_code=422, detail="Resume extraction could not be validated"
            ) from error
        except Exception as error:
            logger.error(
                "Candidate resume AI integration failed exception_module=%s exception_type=%s",
                type(error).__module__,
                type(error).__name__,
            )
            raise HTTPException(status_code=502, detail="AI integration failed") from error
    finally:
        await file.close()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, http_request: Request) -> AnalyzeResponse:
    candidate, job = _candidate_from_request(request)
    ai_config = http_request.app.state.ai_config
    if ai_config is None:
        try:
            ai_config = load_ai_config()
        except ValueError as error:
            raise HTTPException(status_code=503, detail="AI configuration unavailable") from error
    try:
        result = build_analyze_candidate_for_job(ai_config).execute(candidate, job)
    except DomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI integration failed") from error
    return _analysis_response(result)


def _document_response(request: CandidateInput, media_type: str) -> Response:
    candidate = request.to_domain()
    documents = build_generate_candidate_documents().execute(candidate)
    document = documents.docx if media_type != "application/pdf" else documents.pdf
    return Response(
        content=document.content,
        media_type=document.media_type,
        headers={"Content-Disposition": f'attachment; filename="{document.filename}"'},
    )


@router.post("/documents/docx")
def document_docx(request: CandidateInput) -> Response:
    return _document_response(
        request,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/documents/pdf")
def document_pdf(request: CandidateInput) -> Response:
    return _document_response(request, "application/pdf")
