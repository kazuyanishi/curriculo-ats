from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

TStructured = TypeVar("TStructured", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class AIUsage:
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None


class AIUsageObserver(Protocol):
    def record(self, model: str, usage: AIUsage) -> None: ...


class StructuredAIClient(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[TStructured],
    ) -> TStructured: ...
