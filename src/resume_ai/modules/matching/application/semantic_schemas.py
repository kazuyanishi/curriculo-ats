from pydantic import BaseModel, ConfigDict

from resume_ai.modules.matching.domain.entities import MatchStatus


class SemanticMatchDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_index: int
    status: MatchStatus
    evidence_paths: tuple[str, ...] = ()


class SemanticMatchBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decisions: tuple[SemanticMatchDecision, ...]
