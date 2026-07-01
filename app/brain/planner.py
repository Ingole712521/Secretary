"""Execution plan generation (planning only — no execution)."""

from __future__ import annotations

from app.brain.schemas.context import ExecutionContext
from app.brain.schemas.plan import ExecutionPlan, PlanStatus, Task, TaskStatus


class BrainPlanner:
    """Converts user goals into structured execution plans.

    Sprint 2 generates deterministic placeholder plans for architecture
    validation. Future sprints will use LLM-assisted decomposition via
    the ``Planner`` port without changing the Orchestrator interface.

    This class implements the ``Planner`` protocol structurally but
    does not call any LLM provider.
    """

    async def create_plan(
        self,
        goal: str,
        context: ExecutionContext,
    ) -> ExecutionPlan:
        """Create an execution plan from a user goal.

        Generates a structural plan skeleton. Task content is derived
        from the goal string for demonstration purposes only.

        Args:
            goal: Natural-language user goal.
            context: Prepared execution context.

        Returns:
            Draft execution plan with ordered tasks. Plan is not executed.
        """
        conversation_id = (
            context.conversation.id if context.conversation is not None else None
        )
        tasks = self._build_placeholder_tasks(goal)
        return ExecutionPlan(
            goal=goal,
            tasks=tasks,
            status=PlanStatus.DRAFT,
            conversation_id=conversation_id,
            metadata={"planner": "brain.placeholder", "task_count": len(tasks)},
        )

    def _build_placeholder_tasks(self, goal: str) -> list[Task]:
        """Build a deterministic placeholder task list for architecture demos.

        Args:
            goal: User goal used to label the first task.

        Returns:
            Ordered placeholder tasks.
        """
        templates = [
            ("Analyze Request", f"Analyze user goal: {goal}"),
            ("Prepare Environment", "Validate environment and prerequisites"),
            ("Execute Primary Action", "Perform the main requested operation"),
            ("Verify Outcome", "Verify the operation completed successfully"),
            ("Report Result", "Summarize outcome and notify the user"),
        ]
        return [
            Task(
                order=index,
                title=title,
                description=description,
                status=TaskStatus.PENDING,
            )
            for index, (title, description) in enumerate(templates, start=1)
        ]
