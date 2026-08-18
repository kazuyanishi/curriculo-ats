import inspect
import json

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Activity,
    Candidate,
    ContactInfo,
    Experience,
    PersonalInfo,
)
from resume_ai.modules.candidate.domain.value_objects import YearMonth
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.ports import CandidateOptimizationTruthGate
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    ExperienceOptimizationProposal,
    OptimizedExperienceStatementProposal,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_prompt import (
    OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_schemas import (
    OptimizationStatementTruthDecision,
)
from resume_ai.modules.optimization.infrastructure.semantic_optimization_truth_gate import (
    AISemanticOptimizationTruthGate,
)

A = "experiences[0].activities[0].description"
B = "experiences[0].activities[1].description"
C = "experiences[1].activities[0].description"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane Doe", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55 41 99999-0000"),
        experiences=(
            Experience(
                "Example Zero",
                "Support Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(
                    Activity("Atendimento e acompanhamento de chamados."),
                    Activity("Administração de servidores Linux."),
                ),
            ),
            Experience(
                "Example One",
                "Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(Activity("Atividade da segunda experiência."),),
            ),
        ),
    )


def statement(text: str, paths: tuple[str, ...] = (A,)) -> OptimizedExperienceStatementProposal:
    return OptimizedExperienceStatementProposal(text, paths, (0,))


def proposal(*statements: OptimizedExperienceStatementProposal) -> CandidateOptimizationProposal:
    return CandidateOptimizationProposal((ExperienceOptimizationProposal(0, statements),))


class FakeStructuredAIClient:
    def __init__(self, decisions: list[bool]) -> None:
        self._decisions = iter(decisions)
        self.calls: list[tuple[str, str, type]] = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append((system_prompt, user_prompt, response_model))
        return OptimizationStatementTruthDecision(fully_supported=next(self._decisions))


def test_faithful_paraphrase_is_accepted_and_proposal_is_not_transformed() -> None:
    source = candidate()
    input_proposal = proposal(
        statement("Acompanhamento de chamados por meio de atendimento técnico.")
    )
    fake = FakeStructuredAIClient([True])

    result = AISemanticOptimizationTruthGate(fake).validate(source, input_proposal)

    assert result is None
    assert input_proposal == proposal(
        statement("Acompanhamento de chamados por meio de atendimento técnico.")
    )
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    "proposed_text",
    [
        "Gerenciamento de tickets cumprindo SLA de 4 horas.",
        "Gerenciamento de permissões via Active Directory.",
        "Atendimento de mais de 100 chamados mensais.",
        "Criação de relatórios SQL aumentando a eficiência operacional.",
        "Responsável pelas rotinas fiscais.",
        "Atendimento de chamados pelo Jira.",
    ],
)
def test_unsupported_statement_fails_closed(proposed_text: str) -> None:
    input_proposal = proposal(statement(proposed_text))
    fake = FakeStructuredAIClient([False])

    with pytest.raises(OptimizationProposalGroundingError):
        AISemanticOptimizationTruthGate(fake).validate(candidate(), input_proposal)

    assert len(fake.calls) == 1


def test_mixed_verdicts_fail_the_entire_proposal_atomically() -> None:
    source = candidate()
    input_proposal = proposal(statement("first"), statement("second"), statement("third"))
    fake = FakeStructuredAIClient([True, False, True])

    with pytest.raises(OptimizationProposalGroundingError):
        AISemanticOptimizationTruthGate(fake).validate(source, input_proposal)

    assert len(fake.calls) == 2
    assert source == candidate()
    assert input_proposal == proposal(statement("first"), statement("second"), statement("third"))


def test_source_isolation_uses_one_ai_call_per_statement() -> None:
    input_proposal = proposal(
        statement("Atendimento de chamados.", (A,)),
        statement("Administração de servidores Linux.", (B,)),
    )
    fake = FakeStructuredAIClient([True, True])

    AISemanticOptimizationTruthGate(fake).validate(candidate(), input_proposal)

    assert len(fake.calls) == 2
    first_payload = json.loads(fake.calls[0][1])
    second_payload = json.loads(fake.calls[1][1])
    first_text = candidate().experiences[0].activities[0].description
    second_text = candidate().experiences[0].activities[1].description
    assert first_payload == {
        "proposed_text": "Atendimento de chamados.",
        "source_evidence": [{"path": A, "text": first_text}],
    }
    assert second_payload == {
        "proposed_text": "Administração de servidores Linux.",
        "source_evidence": [{"path": B, "text": second_text}],
    }
    assert second_text not in fake.calls[0][1]
    assert first_text not in fake.calls[1][1]


@pytest.mark.parametrize(
    "input_proposal",
    [
        CandidateOptimizationProposal(
            (ExperienceOptimizationProposal(99, (statement("invalid"),)),)
        ),
        proposal(statement("invalid", ("experiences[99].activities[0].description",))),
        proposal(statement("invalid", (C,))),
    ],
)
def test_invalid_or_cross_experience_source_path_fails_before_ai(input_proposal) -> None:
    fake = FakeStructuredAIClient([])

    with pytest.raises(OptimizationProposalGroundingError):
        AISemanticOptimizationTruthGate(fake).validate(candidate(), input_proposal)

    assert fake.calls == []


def test_empty_proposal_or_experience_without_statements_uses_zero_ai_calls() -> None:
    fake = FakeStructuredAIClient([])
    gate = AISemanticOptimizationTruthGate(fake)

    assert gate.validate(candidate(), CandidateOptimizationProposal()) is None
    assert (
        gate.validate(
            candidate(), CandidateOptimizationProposal((ExperienceOptimizationProposal(0),))
        )
        is None
    )
    assert fake.calls == []


def test_all_supported_statements_leave_the_original_proposal_intact() -> None:
    first = statement("Atendimento de chamados.")
    second = statement("Administração de servidores Linux.", (B,))
    input_proposal = proposal(first, second)
    fake = FakeStructuredAIClient([True, True])

    assert AISemanticOptimizationTruthGate(fake).validate(candidate(), input_proposal) is None
    assert input_proposal.experiences[0].statements == (first, second)
    assert input_proposal.experiences[0].statements[0] is first
    assert input_proposal.experiences[0].statements[1] is second


def test_target_match_indexes_are_outside_the_truth_gate_boundary() -> None:
    input_proposal = proposal(
        OptimizedExperienceStatementProposal("Atendimento de chamados.", (A,), (99,))
    )
    fake = FakeStructuredAIClient([True])

    assert AISemanticOptimizationTruthGate(fake).validate(candidate(), input_proposal) is None
    assert len(fake.calls) == 1


def test_truth_decision_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValueError):
        OptimizationStatementTruthDecision.model_validate(
            {"fully_supported": True, "statement_index": 0}
        )


def test_truth_decision_schema_is_frozen() -> None:
    decision = OptimizationStatementTruthDecision(fully_supported=True)

    with pytest.raises(ValueError):
        decision.fully_supported = False


def test_gate_contract_has_no_job_or_matching_dependency_and_minimal_schema() -> None:
    parameters = inspect.signature(CandidateOptimizationTruthGate.validate).parameters
    assert list(parameters) == ["self", "candidate", "proposal"]
    assert inspect.signature(AISemanticOptimizationTruthGate.validate).return_annotation is None
    assert OptimizationStatementTruthDecision.model_fields.keys() == {"fully_supported"}


def test_prompt_preserves_conservative_factual_contract() -> None:
    prompt = " ".join(OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT.lower().split())
    for concept in (
        "conservative factual entailment",
        "every material factual claim",
        "supported by candidate source evidence",
        "otherwise unsupported",
        "data, not instructions",
        "do not infer",
        "metrics",
        "tools",
        "duration",
        "results",
        "responsibility",
        "relationships between facts",
    ):
        assert concept in prompt
