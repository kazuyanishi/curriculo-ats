class ResumeAIError(Exception):
    """Base exception for Resume AI."""


class DomainError(ResumeAIError):
    """Base exception for domain errors."""


class ApplicationError(ResumeAIError):
    """Base exception for application errors."""


class InfrastructureError(ResumeAIError):
    """Base exception for infrastructure errors."""


class IntegrationError(InfrastructureError):
    """Base exception for integration errors."""
