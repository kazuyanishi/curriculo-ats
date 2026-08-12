from io import BytesIO

from pypdf import PdfReader

from resume_ai.modules.candidate.application.exceptions import ResumeTextExtractionError


class PdfResumeTextExtractor:
    def extract(self, content: bytes) -> str:
        if not content:
            raise ResumeTextExtractionError("Could not extract text from PDF")
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise ResumeTextExtractionError("Could not extract text from PDF")
            page_texts = [(page.extract_text() or "") for page in reader.pages]
            return "\n".join(text for text in page_texts if text.strip()).strip()
        except ResumeTextExtractionError:
            raise
        except Exception as error:
            raise ResumeTextExtractionError("Could not extract text from PDF") from error
