from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.exceptions import ProviderNotConfiguredError, StructuredOutputValidationError

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class BaseProvider(ABC):
    provider_name: str
    model_name: str
    model_version: str

    @abstractmethod
    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        """Return output validated against the provided schema."""

    def validate_output(
        self,
        output: Any,
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        try:
            return output_schema.model_validate(output)
        except ValidationError as exc:
            raise StructuredOutputValidationError("Provider returned malformed structured output.") from exc


class DeterministicProvider(BaseProvider):
    provider_name = "deterministic"
    model_name = "deterministic-mvp-reasoner"
    model_version = "0.1.0"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        if prompt_name == "investigation_planning":
            from app.llm.local_planning_model import build_structured_plan

            objective = str(input_payload.get("objective", "")).strip()
            return self.validate_output(build_structured_plan(objective), output_schema)

        raise ProviderNotConfiguredError(f"Deterministic provider has no prompt handler for {prompt_name}.")


class ClaudeProvider(BaseProvider):
    provider_name = "claude"
    model_name = "placeholder"
    model_version = "not_configured"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        raise ProviderNotConfiguredError("ClaudeProvider is a placeholder. Real API integration is out of scope for Sprint 7.")


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    model_name = "placeholder"
    model_version = "not_configured"

    def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredOutput],
    ) -> StructuredOutput:
        raise ProviderNotConfiguredError("OpenAIProvider is a placeholder. Real API integration is out of scope for Sprint 7.")
