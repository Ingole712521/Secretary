"""In-memory prompt provider with default templates."""

from __future__ import annotations

from typing import Any

from app.brain.schemas.prompt import Prompt, PromptTemplate, PromptType


class InMemoryPromptProvider:
    """Process-local prompt provider implementing ``PromptProvider``."""

    def __init__(self) -> None:
        """Initialize with built-in default templates."""
        self._templates: dict[str, PromptTemplate] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default system and safety prompt templates."""
        defaults = [
            PromptTemplate(
                name="system.core",
                prompt_type=PromptType.SYSTEM,
                template=(
                    "You are Jarvis OS, a personal AI operating system. "
                    "Assist the user safely and precisely."
                ),
            ),
            PromptTemplate(
                name="safety.default",
                prompt_type=PromptType.SAFETY,
                template=(
                    "Never execute destructive actions without explicit approval. "
                    "Respect user privacy and scoped permissions."
                ),
            ),
            PromptTemplate(
                name="developer.planning",
                prompt_type=PromptType.DEVELOPER,
                template=(
                    "Generate structured execution plans with clear, ordered steps. "
                    "Do not execute steps — planning only."
                ),
            ),
        ]
        for template in defaults:
            self._templates[template.name] = template

    async def get_template(self, name: str) -> PromptTemplate | None:
        """Retrieve a prompt template by name."""
        return self._templates.get(name)

    async def list_templates(
        self,
        prompt_type: PromptType | None = None,
    ) -> list[PromptTemplate]:
        """List available prompt templates."""
        templates = list(self._templates.values())
        if prompt_type is None:
            return templates
        return [t for t in templates if t.prompt_type == prompt_type]

    async def resolve(
        self,
        template: PromptTemplate,
        variables: dict[str, Any] | None = None,
    ) -> Prompt:
        """Resolve a template into a concrete prompt."""
        content = template.template
        if variables:
            content = content.format(**variables)
        return Prompt(
            prompt_type=template.prompt_type,
            content=content,
            source_template_id=template.id,
            version=template.version.version,
        )
