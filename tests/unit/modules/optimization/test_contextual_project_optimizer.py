import json

import pytest

from resume_ai.modules.candidate.domain.entities import (
    Candidate,
    ContactInfo,
    PersonalInfo,
    Project,
)
from resume_ai.modules.jobs.domain.entities import CriterionCategory, JobCriterion
from resume_ai.modules.matching.domain.entities import CriterionMatch, MatchingResult, MatchStatus
from resume_ai.modules.optimization.application.exceptions import OptimizationProposalGroundingError
from resume_ai.modules.optimization.application.planning import (
    CandidateOptimizationPlan,
    ProjectOptimizationContext,
)
from resume_ai.modules.optimization.infrastructure.contextual_project_optimizer import (
    AIContextualProjectOptimizer,
)
from resume_ai.modules.optimization.infrastructure.contextual_project_schemas import (
    CandidateProjectOptimizationAIResponse,
)

PATH = "projects[0].description"


def candidate() -> Candidate:
    return Candidate(
        PersonalInfo("Jane", "Curitiba", "PR", "Brazil"),
        ContactInfo("jane@example.test", "+55"),
        projects=(Project("API", "API em Python e FastAPI integrada ao PostgreSQL."),),
    )


def matching() -> MatchingResult:
    return MatchingResult(
        (
            CriterionMatch(
                JobCriterion(CriterionCategory.TECHNOLOGY, "Python", "Python required."),
                MatchStatus.MATCHED,
                (PATH,),
            ),
        )
    )


class Client:
    def __init__(self, output):
        self.output, self.calls = output, []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.output


class Gate:
    def __init__(self):
        self.calls = []

    def validate(self, candidate, proposal):
        self.calls.append((candidate, proposal))


def test_project_payload_is_minimal_and_response_is_grounded() -> None:
    client = Client(
        CandidateProjectOptimizationAIResponse.model_validate(
            {
                "projects": [
                    {
                        "project_index": 0,
                        "description": {
                            "text": (
                                "Desenvolveu API em Python com FastAPI integrada ao PostgreSQL."
                            ),
                            "source_paths": [PATH],
                            "target_match_indexes": [0],
                        },
                    }
                ]
            }
        )
    )
    gate = Gate()
    plan = CandidateOptimizationPlan(
        project_contexts=(ProjectOptimizationContext(0, (0,), (PATH,)),)
    )
    proposal = AIContextualProjectOptimizer(client, gate).optimize(candidate(), matching(), plan)
    payload = json.loads(client.calls[0]["user_prompt"])
    assert payload["project_contexts"][0]["candidate_evidence"] == [
        {"path": PATH, "text": candidate().projects[0].description}
    ]
    assert "Jane" not in client.calls[0]["user_prompt"]
    assert proposal.projects[0].description is not None
    assert gate.calls[0][1] is proposal


def test_zero_context_and_cross_binding_fail_closed() -> None:
    empty_client, gate = Client(CandidateProjectOptimizationAIResponse(projects=())), Gate()
    assert (
        AIContextualProjectOptimizer(empty_client, gate)
        .optimize(candidate(), MatchingResult(), CandidateOptimizationPlan())
        .projects
        == ()
    )
    assert empty_client.calls == []
    client = Client(
        CandidateProjectOptimizationAIResponse.model_validate(
            {
                "projects": [
                    {
                        "project_index": 0,
                        "description": {
                            "text": "x",
                            "source_paths": [PATH],
                            "target_match_indexes": [1],
                        },
                    }
                ]
            }
        )
    )
    plan = CandidateOptimizationPlan(
        project_contexts=(ProjectOptimizationContext(0, (0,), (PATH,)),)
    )
    with pytest.raises(OptimizationProposalGroundingError):
        AIContextualProjectOptimizer(client, Gate()).optimize(candidate(), matching(), plan)
