from app.llm.base import StructuredLLM
from app.llm.local_planning_model import LocalStructuredPlanningModel
from app.planning.service import InvestigationPlanner


def build_planner(llm: StructuredLLM | None = None) -> InvestigationPlanner:
    return InvestigationPlanner(llm=llm or LocalStructuredPlanningModel())
