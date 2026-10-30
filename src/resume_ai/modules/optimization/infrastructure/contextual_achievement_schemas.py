from pydantic import BaseModel, ConfigDict


class OptimizedAchievementStatementAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    source_paths: tuple[str, ...]
    target_match_indexes: tuple[int, ...]


class ExperienceAchievementOptimizationAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experience_index: int
    statements: tuple[OptimizedAchievementStatementAI, ...] = ()


class CandidateAchievementOptimizationAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    experiences: tuple[ExperienceAchievementOptimizationAI, ...]
