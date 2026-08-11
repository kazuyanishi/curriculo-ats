from typing import Protocol, TypeVar

from pydantic import BaseModel

TStructured = TypeVar("TStructured", bound=BaseModel)


class StructuredAIClient(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[TStructured],
    ) -> TStructured:
        ...
