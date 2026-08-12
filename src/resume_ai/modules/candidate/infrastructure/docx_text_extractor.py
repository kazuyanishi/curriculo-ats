from io import BytesIO

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from resume_ai.modules.candidate.application.exceptions import ResumeTextExtractionError


class DocxResumeTextExtractor:
    def extract(self, content: bytes) -> str:
        if not content:
            raise ResumeTextExtractionError("Could not extract text from DOCX")
        try:
            document = Document(BytesIO(content))
            blocks = (self._block_text(block) for block in document.iter_inner_content())
            return "\n".join(text for text in blocks if text.strip()).strip()
        except ResumeTextExtractionError:
            raise
        except Exception as error:
            raise ResumeTextExtractionError("Could not extract text from DOCX") from error

    @staticmethod
    def _block_text(block: Paragraph | Table) -> str:
        if isinstance(block, Paragraph):
            return block.text
        if isinstance(block, Table):
            return "\n".join(cell.text for row in block.rows for cell in row.cells)
        return ""
