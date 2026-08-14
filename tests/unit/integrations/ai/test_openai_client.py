import inspect
from typing import get_type_hints

import pytest
from pydantic import BaseModel

import resume_ai.integrations.ai.openai_client as openai_client_module
from resume_ai.integrations.ai.client import (
    AIUsage,
    StructuredAIClient,
    StructuredAIOutputError,
    TStructured,
)
from resume_ai.integrations.ai.config import AIConfig
from resume_ai.integrations.ai.openai_client import OpenAIStructuredAIClient


class ExampleOutput(BaseModel):
    value: str


class FakeResponse:
    def __init__(self, output_parsed: ExampleOutput | None) -> None:
        self.output_parsed = output_parsed


class FakeResponses:
    def __init__(self, output_parsed: ExampleOutput | None) -> None:
        self.output_parsed = output_parsed
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return FakeResponse(self.output_parsed)


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.responses = FakeResponses(ExampleOutput(value="parsed"))
        self.__class__.instances.append(self)


def _generate(client: StructuredAIClient) -> ExampleOutput:
    return client.generate(
        system_prompt="system prompt",
        user_prompt="user prompt",
        response_model=ExampleOutput,
    )


def test_client_passes_api_key_and_uses_model_and_prompts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(openai_client_module, "OpenAI", FakeOpenAI)
    config = AIConfig(api_key="test-key", model="test-model")

    client = OpenAIStructuredAIClient(config)
    result = _generate(client)

    fake = FakeOpenAI.instances[0]
    call = fake.responses.calls[0]
    assert fake.api_key == config.api_key
    assert call["model"] == config.model
    assert call["input"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"},
    ]
    assert call["text_format"] is ExampleOutput
    assert result == ExampleOutput(value="parsed")


def test_client_returns_the_same_parsed_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed = ExampleOutput(value="same instance")

    class OpenAIWithKnownResult(FakeOpenAI):
        def __init__(self, *, api_key: str) -> None:
            self.api_key = api_key
            self.responses = FakeResponses(parsed)

    monkeypatch.setattr(openai_client_module, "OpenAI", OpenAIWithKnownResult)

    result = _generate(OpenAIStructuredAIClient(AIConfig("key", "model")))

    assert result is parsed


def test_client_rejects_missing_parsed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class OpenAIWithoutResult(FakeOpenAI):
        def __init__(self, *, api_key: str) -> None:
            self.api_key = api_key
            self.responses = FakeResponses(None)

    monkeypatch.setattr(openai_client_module, "OpenAI", OpenAIWithoutResult)

    with pytest.raises(
        StructuredAIOutputError,
        match="OpenAI response did not include parsed structured output",
    ):
        _generate(OpenAIStructuredAIClient(AIConfig("key", "model")))


def test_client_reports_usage_before_rejecting_missing_parsed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Usage:
        input_tokens = 1000
        output_tokens = 200

        class input_tokens_details:
            cached_tokens = 400

    class ResponseWithUsage(FakeResponse):
        usage = Usage()

    class ResponsesWithUsage(FakeResponses):
        def parse(self, **kwargs: object) -> ResponseWithUsage:
            self.calls.append(kwargs)
            return ResponseWithUsage(None)

    class OpenAIWithoutParsedOutput(FakeOpenAI):
        def __init__(self, *, api_key: str) -> None:
            self.api_key = api_key
            self.responses = ResponsesWithUsage(None)

    class Observer:
        def __init__(self) -> None:
            self.records: list[tuple[str, AIUsage]] = []

        def record(self, model: str, usage: AIUsage) -> None:
            self.records.append((model, usage))

    monkeypatch.setattr(openai_client_module, "OpenAI", OpenAIWithoutParsedOutput)
    observer = Observer()

    with pytest.raises(StructuredAIOutputError):
        _generate(OpenAIStructuredAIClient(AIConfig("key", "model"), observer))

    assert observer.records == [("model", AIUsage(1000, 400, 200))]


def test_client_reports_optional_usage_to_observer(monkeypatch: pytest.MonkeyPatch) -> None:
    class Usage:
        input_tokens = 1000
        output_tokens = 200

        class input_tokens_details:
            cached_tokens = 400

    class ResponseWithUsage(FakeResponse):
        usage = Usage()

    class ResponsesWithUsage(FakeResponses):
        def parse(self, **kwargs: object) -> ResponseWithUsage:
            self.calls.append(kwargs)
            return ResponseWithUsage(self.output_parsed)

    class OpenAIWithUsage(FakeOpenAI):
        def __init__(self, *, api_key: str) -> None:
            self.api_key = api_key
            self.responses = ResponsesWithUsage(ExampleOutput(value="parsed"))

    class Observer:
        records: list[tuple[str, AIUsage]] = []

        def record(self, model: str, usage: AIUsage) -> None:
            self.records.append((model, usage))

    monkeypatch.setattr(openai_client_module, "OpenAI", OpenAIWithUsage)
    observer = Observer()

    _generate(OpenAIStructuredAIClient(AIConfig("key", "model"), observer))

    assert observer.records == [("model", AIUsage(1000, 400, 200))]


def test_client_satisfies_structured_ai_client_structurally() -> None:
    assert StructuredAIClient not in OpenAIStructuredAIClient.__bases__
    assert callable(_generate)


def test_client_type_hints_match_contract() -> None:
    init_hints = get_type_hints(OpenAIStructuredAIClient.__init__)
    generate_hints = get_type_hints(OpenAIStructuredAIClient.generate)
    parameters = inspect.signature(OpenAIStructuredAIClient.generate).parameters

    assert init_hints["config"] is AIConfig
    assert generate_hints["system_prompt"] is str
    assert generate_hints["user_prompt"] is str
    assert generate_hints["response_model"] == type[TStructured]
    assert generate_hints["return"] is TStructured
    assert all(
        parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in ("system_prompt", "user_prompt", "response_model")
    )
