from pydantic import BaseModel, ConfigDict


class ProjectOptimizationTruthDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    fully_supported: bool
