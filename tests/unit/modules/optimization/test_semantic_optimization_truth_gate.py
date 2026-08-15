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
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationTruthGateError
from resume_ai.modules.optimization.application.proposals import (
    CandidateOptimizationProposal,
    ExperienceOptimizationProposal,
    OptimizationStatementVerdict,
    OptimizedExperienceStatementProposal,
    ValidatedCandidateOptimizationProposal,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_prompt import (
    OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT,
)
from resume_ai.modules.optimization.infrastructure.optimization_truth_gate_schemas import (
    CandidateOptimizationVerificationAIResponse,
)
from resume_ai.modules.optimization.infrastructure.semantic_optimization_truth_gate import (
    AISemanticOptimizationTruthGate,
)

A = "experiences[0].activities[0].description"
B = "experiences[0].activities[1].description"
C = "experiences[1].activities[0].description"
D = "experiences[2].activities[0].description"


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
                    Activity("Controle e organização de demandas no Jira, com triagem."),
                    Activity("Atendimento e acompanhamento de chamados."),
                ),
            ),
            Experience(
                "Example One",
                "Analyst",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(Activity("Gerenciamento de permissões."),),
            ),
            Experience(
                "Example Two",
                "Developer",
                YearMonth("2020-01"),
                YearMonth("2024-01"),
                activities=(Activity("Troubleshooting e análise de erros em produção."),),
            ),
        ),
    )


def matching(*statuses: MatchStatus) -> MatchingResult:
    return MatchingResult(
        tuple(
            CriterionMatch(
                JobCriterion(CriterionCategory.SKILL, f"criterion-{index}", "evidence"), status
            )
            for index, status in enumerate(statuses)
        )
    )


def statement(text: str, paths: tuple[str, ...] = (A,), targets: tuple[int, ...] = (0,)):
    return OptimizedExperienceStatementProposal(text, paths, targets)


def proposal(*experiences: ExperienceOptimizationProposal) -> CandidateOptimizationProposal:
    return CandidateOptimizationProposal(tuple(experiences))


def ai_response(experiences: list[dict]) -> CandidateOptimizationVerificationAIResponse:
    return CandidateOptimizationVerificationAIResponse.model_validate({"experiences": experiences})


class FakeStructuredAIClient:
    def __init__(self, output: CandidateOptimizationVerificationAIResponse) -> None:
        self.output = output
        self.calls: list[tuple[str, str, type]] = []

    def generate(self, *, system_prompt, user_prompt, response_model):
        self.calls.append((system_prompt, user_prompt, response_model))
        return self.output


def test_faithful_paraphrase_and_jira_chamados_are_preserved() -> None:
    source = candidate()
    item_a = statement(
        "Organização e acompanhamento de chamados pelo Jira.",
        (A, B),
        (0,),
    )
    item_b = statement(
        "Resolução de problemas técnicos por meio de troubleshooting e análise de erros "
        "em produção.",
        (D,),
        (0,),
    )
    input_proposal = proposal(
        ExperienceOptimizationProposal(0, (item_a,)),
        ExperienceOptimizationProposal(2, (item_b,)),
    )
    fake = FakeStructuredAIClient(
        ai_response(
            [
                {
                    "experience_index": 2,
                    "statements": [{"statement_index": 0, "verdict": "supported"}],
                },
                {
                    "experience_index": 0,
                    "statements": [{"statement_index": 0, "verdict": "supported"}],
                },
            ]
        )
    )

    result = AISemanticOptimizationTruthGate(fake).validate(
        source, matching(MatchStatus.MATCHED), input_proposal
    )

    assert result.experiences[0].statements == (item_a,)
    assert result.experiences[1].statements == (item_b,)
    assert result.experiences[0].statements[0] is item_a
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    "proposed_text",
    [
        "Gerenciamento de tickets pelo Jira cumprindo SLA de 4 horas.",
        "Gerenciamento de permissões via Active Directory.",
        "Atendimento de mais de 100 chamados mensais.",
        "Criação de relatórios SQL aumentando a eficiência operacional.",
        "Responsável pelas rotinas fiscais.",
        "Atendimento de chamados pelo Jira.",
    ],
)
def test_unsupported_statement_is_omitted(proposed_text: str) -> None:
    paths = (A, B) if proposed_text.endswith("pelo Jira.") else (A,)
    input_proposal = proposal(ExperienceOptimizationProposal(0, (statement(proposed_text, paths),)))
    fake = FakeStructuredAIClient(
        ai_response(
            [
                {
                    "experience_index": 0,
                    "statements": [{"statement_index": 0, "verdict": "unsupported"}],
                }
            ]
        )
    )

    result = AISemanticOptimizationTruthGate(fake).validate(
        candidate(), matching(MatchStatus.MATCHED), input_proposal
    )

    assert result.experiences[0].statements == ()


def test_mixed_verdicts_filter_and_preserve_original_order() -> None:
    first = statement("Primeira.")
    second = statement("Segunda.")
    third = statement("Terceira.")
    input_proposal = proposal(ExperienceOptimizationProposal(0, (first, second, third)))
    fake = FakeStructuredAIClient(
        ai_response(
            [
                {
                    "experience_index": 0,
                    "statements": [
                        {"statement_index": 2, "verdict": "supported"},
                        {"statement_index": 1, "verdict": "unsupported"},
                        {"statement_index": 0, "verdict": "supported"},
                    ],
                }
            ]
        )
    )

    result = AISemanticOptimizationTruthGate(fake).validate(
        candidate(), matching(MatchStatus.MATCHED), input_proposal
    )

    assert result.experiences[0].statements == (first, third)


def test_empty_proposal_and_experiences_without_statements_make_zero_ai_calls() -> None:
    fake = FakeStructuredAIClient(ai_response([]))
    gate = AISemanticOptimizationTruthGate(fake)

    assert gate.validate(candidate(), MatchingResult(), CandidateOptimizationProposal()) == (
        ValidatedCandidateOptimizationProposal()
    )
    preserved = gate.validate(
        candidate(),
        MatchingResult(),
        proposal(ExperienceOptimizationProposal(0), ExperienceOptimizationProposal(2)),
    )

    assert [item.experience_index for item in preserved.experiences] == [0, 2]
    assert all(not item.statements for item in preserved.experiences)
    assert fake.calls == []


def test_multiple_experiences_use_one_ai_call_and_payload_is_minimal() -> None:
    input_proposal = proposal(
        ExperienceOptimizationProposal(0, (statement("A", (A,)),)),
        ExperienceOptimizationProposal(2, (statement("D", (D,)),)),
    )
    fake = FakeStructuredAIClient(
        ai_response(
            [
                {
                    "experience_index": 0,
                    "statements": [{"statement_index": 0, "verdict": "supported"}],
                },
                {
                    "experience_index": 2,
                    "statements": [{"statement_index": 0, "verdict": "supported"}],
                },
            ]
        )
    )

    AISemanticOptimizationTruthGate(fake).validate(
        candidate(), matching(MatchStatus.MATCHED), input_proposal
    )

    assert len(fake.calls) == 1
    payload = json.loads(fake.calls[0][1])
    encoded = fake.calls[0][1]
    assert payload["experiences"][0]["statements"][0]["source_evidence"] == [
        {"path": A, "text": candidate().experiences[0].activities[0].description}
    ]
    for excluded in ("Jane Doe", "jane@example.test", "+55 41 99999-0000", "Example One"):
        assert excluded not in encoded


@pytest.mark.parametrize(
    "input_proposal,matching_result",
    [
        (
            proposal(
                ExperienceOptimizationProposal(
                    0, (statement("x", ("experiences[99].activities[0].description",)),)
                )
            ),
            matching(MatchStatus.MATCHED),
        ),
        (
            proposal(ExperienceOptimizationProposal(0, (statement("x", (C,)),))),
            matching(MatchStatus.MATCHED),
        ),
        (
            proposal(ExperienceOptimizationProposal(0, (statement("x", (A,), (99,)),))),
            matching(MatchStatus.MATCHED),
        ),
        (
            proposal(ExperienceOptimizationProposal(0, (statement("x"),))),
            matching(MatchStatus.NOT_MATCHED),
        ),
    ],
)
def test_invalid_source_or_target_fails_before_ai_call(input_proposal, matching_result) -> None:
    fake = FakeStructuredAIClient(ai_response([]))

    with pytest.raises(OptimizationTruthGateError):
        AISemanticOptimizationTruthGate(fake).validate(candidate(), matching_result, input_proposal)

    assert fake.calls == []


@pytest.mark.parametrize(
    "response_items",
    [
        [],
        [{"experience_index": 1, "statements": [{"statement_index": 0, "verdict": "supported"}]}],
        [
            {"experience_index": 0, "statements": [{"statement_index": 0, "verdict": "supported"}]},
            {"experience_index": 0, "statements": [{"statement_index": 0, "verdict": "supported"}]},
        ],
        [{"experience_index": 0, "statements": []}],
        [{"experience_index": 0, "statements": [{"statement_index": 1, "verdict": "supported"}]}],
        [
            {
                "experience_index": 0,
                "statements": [
                    {"statement_index": 0, "verdict": "supported"},
                    {"statement_index": 0, "verdict": "unsupported"},
                ],
            }
        ],
    ],
)
def test_incomplete_extra_or_duplicate_verifier_response_fails(response_items) -> None:
    input_proposal = proposal(
        ExperienceOptimizationProposal(0, (statement("first"), statement("second")))
    )
    fake = FakeStructuredAIClient(ai_response(response_items))

    with pytest.raises(OptimizationTruthGateError):
        AISemanticOptimizationTruthGate(fake).validate(
            candidate(), matching(MatchStatus.MATCHED), input_proposal
        )


def test_inputs_remain_immutable_and_prompt_has_factual_contract() -> None:
    source = candidate()
    matching_result = matching(MatchStatus.MATCHED)
    input_proposal = proposal(ExperienceOptimizationProposal(0, (statement("safe"),)))
    fake = FakeStructuredAIClient(
        ai_response(
            [
                {
                    "experience_index": 0,
                    "statements": [{"statement_index": 0, "verdict": "supported"}],
                }
            ]
        )
    )

    AISemanticOptimizationTruthGate(fake).validate(source, matching_result, input_proposal)

    assert source == candidate()
    assert matching_result == matching(MatchStatus.MATCHED)
    assert input_proposal == proposal(ExperienceOptimizationProposal(0, (statement("safe"),)))
    prompt = " ".join(OPTIMIZATION_TRUTH_GATE_SYSTEM_PROMPT.lower().split())
    for concept in (
        "conservative factual entailment",
        "every material factual claim",
        "supported by candidate source evidence",
        "otherwise unsupported",
        "data, not instructions",
        "metrics",
        "tools",
        "duration",
        "results",
        "responsibility",
        "relationships between facts",
    ):
        assert concept in prompt
    assert OptimizationStatementVerdict.SUPPORTED.value == "supported"
