"""PawPal+ logic layer.

Backend classes for the pet care planning assistant. This module holds the
"skeleton" generated from our UML: class names, attributes, and empty method
stubs. Scheduling behavior will be implemented incrementally.

Class overview:
    CareTask   - one unit of pet care (walk, feeding, meds, etc.)
    Pet        - an animal and the tasks that belong to it
    Owner      - the user, their pets, and their constraints/preferences
    Scheduler  - builds a plan from an Owner under their constraints
    DailyPlan  - the resulting schedule plus the reasoning behind it
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Order used to turn priority strings into sortable numbers (higher = more urgent).
PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}


@dataclass
class CareTask:
    """One unit of pet care (a walk, feeding, meds, grooming, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"          # "low" | "medium" | "high"
    preferred_time: str | None = None  # e.g. "morning" or "08:00"
    recurrence: str = "daily"          # "daily" | "weekly" | "once"
    category: str = "general"          # walk, feeding, meds, grooming, ...

    def priority_score(self) -> int:
        """Return a sortable integer for this task's priority."""
        raise NotImplementedError

    def is_due_today(self, day) -> bool:
        """Return True if this task should happen on the given day."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Return a readable label for use in the plan display."""
        raise NotImplementedError


@dataclass
class Pet:
    """The animal that care tasks belong to."""

    name: str
    species: str = "other"  # "dog" | "cat" | "other"
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: CareTask) -> None:
        """Remove a care task from this pet."""
        raise NotImplementedError

    def tasks_due(self, day) -> list[CareTask]:
        """Return this pet's tasks that are due on the given day."""
        raise NotImplementedError


@dataclass
class Owner:
    """The user, their pets, and the constraints the plan must respect."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 0
    preferences: dict = field(default_factory=dict)  # e.g. {"walk": "morning"}

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def all_tasks_due(self, day) -> list[CareTask]:
        """Gather tasks due on the given day across all of this owner's pets."""
        raise NotImplementedError


class Scheduler:
    """Builds a DailyPlan for an owner, respecting time and priority constraints."""

    def __init__(self, owner: Owner, day) -> None:
        self.owner = owner
        self.day = day

    def build_plan(self) -> "DailyPlan":
        """Choose and order tasks under the owner's constraints; return a DailyPlan."""
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks ordered by scheduling importance (e.g. priority)."""
        raise NotImplementedError

    def _fits(self, task: CareTask, remaining_time: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        raise NotImplementedError


@dataclass
class DailyPlan:
    """The generated schedule plus the reasoning behind each decision."""

    scheduled: list = field(default_factory=list)      # list of (time, CareTask)
    skipped: list[CareTask] = field(default_factory=list)
    reasons: dict = field(default_factory=dict)        # task -> explanation string

    def explain(self) -> str:
        """Return a human-readable explanation of why each task was chosen/placed."""
        raise NotImplementedError

    def to_table(self) -> list:
        """Return rows suitable for display in the Streamlit UI."""
        raise NotImplementedError

    def total_time(self) -> int:
        """Return the total scheduled minutes."""
        raise NotImplementedError
