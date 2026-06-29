from app.ai.router import ProviderRouter
from app.ai.service import AIReasoningService
from app.core.config import settings
from app.planning.service import InvestigationPlanner


def build_planner(ai_reasoning: AIReasoningService | None = None) -> InvestigationPlanner:
    return InvestigationPlanner(
        ai_reasoning=ai_reasoning
        or AIReasoningService(router=ProviderRouter(default_provider=settings.ai_provider))
    )
