from fastapi import FastAPI

from resume_ai.integrations.ai.config import AIConfig
from resume_ai.interfaces.api.routes import router


def create_app(ai_config: AIConfig | None = None) -> FastAPI:
    app = FastAPI(title="Resume AI")
    app.state.ai_config = ai_config
    app.include_router(router, prefix="/api/v1")
    return app
