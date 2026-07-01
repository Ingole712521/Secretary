"""Prompt template management and resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.brain.exceptions import PromptNotFoundError
from app.brain.schemas.prompt import Prompt, PromptTemplate, PromptType
from app.brain.stores.prompt_provider import InMemoryPromptProvider

if TYPE_CHECKING:
    from app.brain.interfaces.prompt_provider import PromptProvider


class PromptManager:
    """Manages system, developer, user, tool, and safety prompts.

    Handles template registration, versioning metadata, and resolution.
    Does not call LLM providers directly.

    Attributes:
        _provider: Prompt storage and resolution port.
    """

    def __init__(self, provider: PromptProvider) -> None:
        """Initialize with a prompt provider adapter.

        Args:
            provider: Prompt storage port implementation.
        """
        self._provider = provider

    async def register(self, template: PromptTemplate) -> PromptTemplate:
        """Register a new prompt template.

        Args:
            template: Template to register.

        Returns:
            Registered template.

        Note:
            In-memory provider stores templates by name via direct dict
            access in Sprint 2. Persistent providers will implement
            proper registration in future sprints.
        """
        if isinstance(self._provider, InMemoryPromptProvider):
            self._provider._templates[template.name] = template
        return template

    async def get_template(self, name: str) -> PromptTemplate:
        """Retrieve a template by name.

        Args:
            name: Template name.

        Returns:
            Matching template.

        Raises:
            PromptNotFoundError: If the template does not exist.
        """
        template = await self._provider.get_template(name)
        if template is None:
            raise PromptNotFoundError(name)
        return template

    async def resolve(
        self,
        name: str,
        variables: dict[str, Any] | None = None,
    ) -> Prompt:
        """Resolve a named template into a concrete prompt.

        Args:
            name: Template name.
            variables: Optional template variables.

        Returns:
            Resolved prompt.
        """
        template = await self.get_template(name)
        return await self._provider.resolve(template, variables)

    async def get_prompts_by_type(self, prompt_type: PromptType) -> list[Prompt]:
        """Resolve all templates of a given type.

        Args:
            prompt_type: Prompt category filter.

        Returns:
            List of resolved prompts.
        """
        templates = await self._provider.list_templates(prompt_type)
        return [await self._provider.resolve(t) for t in templates]

    async def get_active_prompts(self) -> list[Prompt]:
        """Return all active system and safety prompts.

        Returns:
            Resolved system and safety prompts for context assembly.
        """
        system = await self.get_prompts_by_type(PromptType.SYSTEM)
        safety = await self.get_prompts_by_type(PromptType.SAFETY)
        developer = await self.get_prompts_by_type(PromptType.DEVELOPER)
        return [*system, *safety, *developer]
