from openai import OpenAI

from resume_ai.integrations.ai.client import AIUsage, AIUsageObserver, TStructured
from resume_ai.integrations.ai.config import AIConfig


class OpenAIStructuredAIClient:
    def __init__(self, config: AIConfig, observer: AIUsageObserver | None = None) -> None:
        self._client = OpenAI(api_key=config.api_key)
        self._model = config.model
        self._observer = observer

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[TStructured],
    ) -> TStructured:
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text_format=response_model,
        )
        result = response.output_parsed
        if result is None:
            raise ValueError("OpenAI response did not include parsed structured output")
        if self._observer is not None:
            usage = getattr(response, "usage", None)
            details = getattr(usage, "input_tokens_details", None)
            self._observer.record(
                self._model,
                AIUsage(
                    input_tokens=getattr(usage, "input_tokens", None),
                    cached_input_tokens=getattr(details, "cached_tokens", None),
                    output_tokens=getattr(usage, "output_tokens", None),
                ),
            )
        return result
