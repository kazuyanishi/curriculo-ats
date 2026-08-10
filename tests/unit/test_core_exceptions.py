import pytest

from resume_ai.core.exceptions import (
    ApplicationError,
    DomainError,
    InfrastructureError,
    IntegrationError,
    ResumeAIError,
)


def test_base_error_preserves_exception_behavior() -> None:
    error = ResumeAIError("failure")

    assert isinstance(error, Exception)
    assert str(error) == "failure"


@pytest.mark.parametrize(
    "error_type",
    [DomainError, ApplicationError, InfrastructureError],
)
def test_core_errors_inherit_from_resume_ai_error(error_type: type[ResumeAIError]) -> None:
    assert issubclass(error_type, ResumeAIError)
    assert issubclass(error_type, Exception)


def test_integration_error_inherits_from_infrastructure_and_resume_ai() -> None:
    error = IntegrationError("provider unavailable")

    assert issubclass(IntegrationError, InfrastructureError)
    assert issubclass(IntegrationError, ResumeAIError)
    assert isinstance(error, InfrastructureError)
    assert isinstance(error, ResumeAIError)


def test_domain_error_can_be_caught_by_resume_ai_error() -> None:
    with pytest.raises(ResumeAIError, match="invalid domain"):
        raise DomainError("invalid domain")


def test_integration_error_can_be_caught_by_infrastructure_error() -> None:
    with pytest.raises(InfrastructureError, match="provider unavailable"):
        raise IntegrationError("provider unavailable")
