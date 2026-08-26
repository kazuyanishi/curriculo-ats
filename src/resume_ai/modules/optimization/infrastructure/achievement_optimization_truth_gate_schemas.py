from pydantic import BaseModel, ConfigDict


class AchievementOptimizationStatementTruthDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fully_supported: bool
