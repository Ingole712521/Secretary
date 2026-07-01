"""Execution plan and task schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.utils.date import utc_now


class TaskStatus(StrEnum):
    """Lifecycle status of an individual plan task."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(StrEnum):
    """Lifecycle status of an execution plan."""

    DRAFT = "draft"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """A single step within an execution plan.

    Attributes:
        id: Unique task identifier.
        order: Execution order (1-based).
        title: Short task title.
        description: Detailed task description.
        dependencies: IDs of tasks that must complete first.
        status: Current task status.
        metadata: Optional task metadata for agents/tools.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    order: int = Field(ge=1)
    title: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Structured plan produced by the Planner.

    The Planner generates plans but does not execute them.
    Execution is delegated to future agent orchestration layers.

    Attributes:
        id: Unique plan identifier.
        goal: Original user goal in natural language.
        tasks: Ordered list of plan tasks.
        status: Current plan status.
        conversation_id: Associated conversation, if any.
        metadata: Plan-level metadata.
        created_at: UTC creation timestamp.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    goal: str
    tasks: list[Task] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    conversation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
