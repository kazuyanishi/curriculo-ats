from typing import Protocol


class ResumeTextExtractor(Protocol):
    def extract(self, content: bytes) -> str:
        ...
