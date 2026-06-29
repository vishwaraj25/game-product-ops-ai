from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.exceptions import AIReasoningError, StructuredOutputValidationError
from app.ai.prompts import PromptManager
from app.ai.providers import BaseProvider
from app.ai.router import ProviderRouter

StructuredResult = TypeVar("StructuredResult", bound=BaseModel)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIReasoningTrace:
    task: str
    prompt_name: str
    prompt_version: str
    provider_name: str
    model_name: str
    model_version: str


class AIReasoningService:
    def __init__(
        self,
        *,
        prompts: PromptManager | None = None,
        router: ProviderRouter | None = None,
        fallback_provider: BaseProvider | None = None,
        max_attempts: int = 2,
    ) -> None:
        self.prompts = prompts or PromptManager()
        self.router = router or ProviderRouter()
        self.fallback_provider = fallback_provider
        self.max_attempts = max(1, max_attempts)

    def generate_structured(
        self,
        *,
        task: str,
        prompt_name: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredResult],
        provider_name: str | None = None,
    ) -> StructuredResult:
        prompt = self.prompts.get(prompt_name)
        provider = self.router.get(provider_name)
        trace = AIReasoningTrace(
            task=task,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            provider_name=provider.provider_name,
            model_name=provider.model_name,
            model_version=provider.model_version,
        )

        logger.info("ai_reasoning.started", extra={"trace": trace.__dict__})
        try:
            result = self._attempt_provider(
                provider=provider,
                trace=trace,
                instructions=prompt.instructions,
                input_payload=input_payload,
                output_schema=output_schema,
            )
            logger.info("ai_reasoning.completed", extra={"trace": trace.__dict__})
            return result
        except AIReasoningError:
            if not self.fallback_provider:
                logger.exception("ai_reasoning.failed", extra={"trace": trace.__dict__})
                raise

            fallback_trace = AIReasoningTrace(
                task=task,
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                provider_name=self.fallback_provider.provider_name,
                model_name=self.fallback_provider.model_name,
                model_version=self.fallback_provider.model_version,
            )
            logger.warning("ai_reasoning.fallback_started", extra={"trace": fallback_trace.__dict__})
            result = self._attempt_provider(
                provider=self.fallback_provider,
                trace=fallback_trace,
                instructions=prompt.instructions,
                input_payload=input_payload,
                output_schema=output_schema,
            )
            logger.info("ai_reasoning.fallback_completed", extra={"trace": fallback_trace.__dict__})
            return result

    def _attempt_provider(
        self,
        *,
        provider: BaseProvider,
        trace: AIReasoningTrace,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredResult],
    ) -> StructuredResult:
        last_error: AIReasoningError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(
                    "ai_reasoning.provider_attempt",
                    extra={"trace": trace.__dict__, "attempt": attempt},
                )
                return provider.generate_structured(
                    prompt_name=trace.prompt_name,
                    prompt_version=trace.prompt_version,
                    instructions=instructions,
                    input_payload=input_payload,
                    output_schema=output_schema,
                )
            except StructuredOutputValidationError as exc:
                last_error = exc
                logger.warning(
                    "ai_reasoning.validation_retry",
                    extra={"trace": trace.__dict__, "attempt": attempt},
                )

        if last_error:
            raise last_error
        raise AIReasoningError("Provider failed without an explicit error.")
