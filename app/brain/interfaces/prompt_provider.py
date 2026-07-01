"""Prompt provider port interface."""

from __future__ import annotations

from typing import Any, Protocol

from app.brain.schemas.prompt import Prompt, PromptTemplate, PromptType


class PromptProvider(Protocol):
    """Port for loading and resolving prompt templates.

    Separates prompt storage from the PromptManager orchestration layer.
    """

    async def get_template(self, name: str) -> PromptTemplate | None:
        """Retrieve a prompt template by name.

        Args:
            name: Template name.

        Returns:
            Template if found, otherwise None.
        """
        ...

    async def list_templates(
        self,
        prompt_type: PromptType | None = None,
    ) -> list[PromptTemplate]:
        """List available prompt templates.

        Args:
            prompt_type: Optional filter by prompt type.

        Returns:
            Matching prompt templates.
        """
        ...

    async def resolve(
        self,
        template: PromptTemplate,
        variables: dict[str, Any] | None = None,
    ) -> Prompt:
        """Resolve a template into a concrete prompt.

        Args:
            template: Template to resolve.
            variables: Template variable values.

        Returns:
            Resolved prompt with interpolated content.
        """
        ...
