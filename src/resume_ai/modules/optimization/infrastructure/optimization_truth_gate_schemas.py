from pydantic import BaseModel, ConfigDict


class OptimizationStatementTruthDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fully_supported: bool
