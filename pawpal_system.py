"""PawPal+ logic layer.

Backend classes for the pet care planning assistant, implemented from our UML.

Class overview:
    CareTask   - one unit of pet care (walk, feeding, meds, etc.) with completion status
    Pet        - an animal and the tasks that belong to it
    Owner      - the user, their pets, and their constraints/preferences
    Scheduler  - the "brain": retrieves, organizes, and plans tasks across pets
    DailyPlan  - the resulting schedule plus the reasoning behind it
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


# Map priority strings to sortable numbers (higher = more urgent).
PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}


@dataclass
class CareTask:
    """One unit of pet care (a walk, feeding, meds, grooming, etc.).

    This is our "Task": a single activity with a description, how long it
    takes, how often it repeats, and whether it has been completed.
    """

    title: str
    duration_minutes: int
    priority: str = "medium"           # "low" | "medium" | "high"
    preferred_time: str | None = None  # e.g. "morning" or "08:00"
    recurrence: str = "daily"          # "daily" | "weekly" | "once"
    category: str = "general"          # walk, feeding, meds, grooming, ...
    completed: bool = False

    def priority_score(self) -> int:
        """Return a sortable integer for this task's priority (unknown -> 0)."""
        return PRIORITY_SCORES.get(self.priority.lower(), 0)

    def is_due_today(self, day=None) -> bool:
        """Return True if this task still needs to happen on the given day.

        A completed task is never "due". Daily tasks are always due; a one-off
        ("once") is due until completed; weekly tasks are treated as due here
        (a real calendar check would compare `day` to the task's weekday).
        """
        if self.completed:
            return False
        return self.recurrence in ("daily", "once", "weekly")

    def mark_complete(self) -> None:
        """Mark this task complete."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset this task to not complete."""
        self.completed = False

    def __str__(self) -> str:
        """Return a readable label for use in the plan display."""
        box = "x" if self.completed else " "
        return f"[{box}] {self.title} ({self.duration_minutes} min, {self.priority})"


@dataclass
class Pet:
    """The animal that care tasks belong to."""

    name: str
    species: str = "other"  # "dog" | "cat" | "other"
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: CareTask) -> None:
        """Remove a care task from this pet (no error if it isn't present)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def tasks_due(self, day=None) -> list[CareTask]:
        """Return this pet's tasks that are due on the given day."""
        return [task for task in self.tasks if task.is_due_today(day)]


@dataclass
class Owner:
    """The user, their pets, and the constraints the plan must respect."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 0
    preferences: dict = field(default_factory=dict)  # e.g. {"walk": "morning"}

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def all_tasks_due(self, day=None) -> list[CareTask]:
        """Gather tasks due on the given day across all of this owner's pets."""
        due: list[CareTask] = []
        for pet in self.pets:
            due.extend(pet.tasks_due(day))
        return due


class Scheduler:
    """The brain: retrieves, organizes, and plans tasks across an owner's pets."""

    DEFAULT_START_HOUR = 8  # plans start at 08:00 by default

    def __init__(self, owner: Owner, day=None) -> None:
        """Create a scheduler for a given owner and target day."""
        self.owner = owner
        self.day = day

    def build_plan(self, start_hour: int | None = None) -> "DailyPlan":
        """Choose and order tasks under the owner's time budget; return a DailyPlan.

        Tasks are sorted by priority, then packed into the available minutes.
        Each task gets a clock time and a short reason; anything that doesn't
        fit is recorded as skipped with an explanation.
        """
        if start_hour is None:
            start_hour = self.DEFAULT_START_HOUR

        due = self._sort_tasks(self.owner.all_tasks_due(self.day))
        plan = DailyPlan()
        remaining = self.owner.available_minutes
        current = datetime(2000, 1, 1, start_hour, 0)  # date is arbitrary; time matters

        for task in due:
            if self._fits(task, remaining):
                time_str = current.strftime("%H:%M")
                plan.scheduled.append((time_str, task))
                plan.reasons[task.title] = (
                    f"Placed at {time_str}: {task.priority} priority, "
                    f"fits in the {remaining} min still available."
                )
                remaining -= task.duration_minutes
                current += timedelta(minutes=task.duration_minutes)
            else:
                plan.skipped.append(task)
                plan.reasons[task.title] = (
                    f"Skipped: needs {task.duration_minutes} min but only "
                    f"{remaining} min left in the day."
                )
        return plan

    def _sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Order tasks by priority (high first), then shorter tasks, then title."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_score(), t.duration_minutes, t.title),
        )

    def _fits(self, task: CareTask, remaining_time: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        return task.duration_minutes <= remaining_time


@dataclass
class DailyPlan:
    """The generated schedule plus the reasoning behind each decision."""

    scheduled: list = field(default_factory=list)      # list of (time_str, CareTask)
    skipped: list[CareTask] = field(default_factory=list)
    reasons: dict = field(default_factory=dict)        # task title -> explanation

    def explain(self) -> str:
        """Return a human-readable explanation of why each task was chosen/placed."""
        if not self.scheduled and not self.skipped:
            return "No tasks to plan."
        lines = []
        for time_str, task in self.scheduled:
            lines.append(f"{time_str} — {task.title}: {self.reasons.get(task.title, '')}")
        for task in self.skipped:
            lines.append(f"(skipped) {task.title}: {self.reasons.get(task.title, '')}")
        return "\n".join(lines)

    def to_table(self) -> list:
        """Return rows suitable for display in the Streamlit UI."""
        return [
            {
                "time": time_str,
                "title": task.title,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
            }
            for time_str, task in self.scheduled
        ]

    def total_time(self) -> int:
        """Return the total scheduled minutes."""
        return sum(task.duration_minutes for _, task in self.scheduled)
