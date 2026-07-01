"""Planner port interface."""

from __future__ import annotations

from typing import Protocol

from app.brain.schemas.context import ExecutionContext
from app.brain.schemas.plan import ExecutionPlan


class Planner(Protocol):
    """Port for converting user goals into execution plans.

    Implementations generate plans only. They must not execute tasks.
    """

    async def create_plan(
        self,
        goal: str,
        context: ExecutionContext,
    ) -> ExecutionPlan:
        """Create an execution plan from a user goal.

        Args:
            goal: Natural-language user goal.
            context: Prepared execution context.

        Returns:
            Structured execution plan with ordered tasks.
        """
        ...
