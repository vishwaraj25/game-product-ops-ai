from app.ai.router import ProviderRouter
from app.ai.service import AIReasoningService
from app.core.config import settings


def build_ai_reasoning_service() -> AIReasoningService:
    return AIReasoningService(router=ProviderRouter(default_provider=settings.ai_provider))
