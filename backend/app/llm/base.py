from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class StructuredLLM(ABC):
    provider_name: str
    model_name: str
    model_version: str

    @abstractmethod
    def generate_structured(
        self,
        *,
        task: str,
        instructions: str,
        input_payload: dict[str, Any],
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        """Return validated structured output for a task.

        Implementations may call a remote LLM, a local model, or a deterministic
        development model. Callers depend only on this abstraction.
        """
