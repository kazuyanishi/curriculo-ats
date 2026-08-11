import inspect
from typing import get_type_hints

from pydantic import BaseModel

from resume_ai.integrations.ai.client import StructuredAIClient, TStructured


class ExampleStructuredOutput(BaseModel):
    value: str


class FakeStructuredAIClient:
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ExampleStructuredOutput],
    ) -> ExampleStructuredOutput:
        return response_model(value=f"{system_prompt}: {user_prompt}")


def _generate(client: StructuredAIClient) -> ExampleStructuredOutput:
    return client.generate(
        system_prompt="System instruction",
        user_prompt="User content",
        response_model=ExampleStructuredOutput,
    )


def test_structured_ai_client_supports_structural_implementations() -> None:
    result = _generate(FakeStructuredAIClient())

    assert isinstance(result, ExampleStructuredOutput)
    assert result.value == "System instruction: User content"


def test_structured_ai_client_generate_contract() -> None:
    hints = get_type_hints(StructuredAIClient.generate)
    parameters = inspect.signature(StructuredAIClient.generate).parameters

    assert hints["system_prompt"] is str
    assert hints["user_prompt"] is str
    assert hints["response_model"] == type[TStructured]
    assert hints["return"] is TStructured
    assert all(
        parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in ("system_prompt", "user_prompt", "response_model")
    )


def test_structured_ai_client_typevar_is_bound_to_basemodel() -> None:
    assert TStructured.__bound__ is BaseModel
