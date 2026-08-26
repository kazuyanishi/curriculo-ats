from pydantic import BaseModel, ConfigDict


class OptimizedProjectDescriptionAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    source_paths: tuple[str, ...]
    target_match_indexes: tuple[int, ...]


class ProjectOptimizationAI(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    project_index: int
    description: OptimizedProjectDescriptionAI | None = None


class CandidateProjectOptimizationAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    projects: tuple[ProjectOptimizationAI, ...]
