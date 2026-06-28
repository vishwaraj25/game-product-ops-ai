from __future__ import annotations

from app.tools.base import InvestigationTool


class ToolRegistry:
    def __init__(self, tools: list[InvestigationTool] | None = None) -> None:
        self._tools: dict[str, InvestigationTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: InvestigationTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> InvestigationTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise UnknownToolError(f"Tool is not registered: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tools)


class UnknownToolError(Exception):
    pass
