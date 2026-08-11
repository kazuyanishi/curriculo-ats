from openai import OpenAI

from resume_ai.integrations.ai.client import TStructured
from resume_ai.integrations.ai.config import AIConfig


class OpenAIStructuredAIClient:
    def __init__(self, config: AIConfig) -> None:
        self._client = OpenAI(api_key=config.api_key)
        self._model = config.model

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
        return result
