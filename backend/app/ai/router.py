from __future__ import annotations

from app.ai.exceptions import ProviderNotConfiguredError
from app.ai.providers import BaseProvider, ClaudeProvider, DeterministicProvider, OpenAIProvider


class ProviderRouter:
    def __init__(
        self,
        *,
        default_provider: str = "deterministic",
        providers: dict[str, BaseProvider] | None = None,
    ) -> None:
        self.default_provider = default_provider
        self._providers = providers or {
            "deterministic": DeterministicProvider(),
            "claude": ClaudeProvider(),
            "openai": OpenAIProvider(),
        }

    def get(self, provider_name: str | None = None) -> BaseProvider:
        selected = provider_name or self.default_provider
        try:
            return self._providers[selected]
        except KeyError as exc:
            raise ProviderNotConfiguredError(f"Unknown AI provider: {selected}") from exc
