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
from datetime import date, datetime, timedelta


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
    due_date: date | None = None       # when this occurrence is due

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

    def next_due_date(self) -> date | None:
        """Return the next due date based on recurrence; None if it doesn't repeat."""
        base = self.due_date or date.today()
        if self.recurrence == "daily":
            return base + timedelta(days=1)   # daily -> today + 1 day
        if self.recurrence == "weekly":
            return base + timedelta(weeks=1)  # weekly -> today + 7 days
        return None                           # "once" tasks do not recur

    def next_occurrence(self) -> "CareTask | None":
        """Return a fresh, incomplete copy of this task for its next due date.

        Returns None for one-off ("once") tasks, which have no next occurrence.
        """
        upcoming = self.next_due_date()
        if upcoming is None:
            return None
        return CareTask(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
            recurrence=self.recurrence,
            category=self.category,
            completed=False,
            due_date=upcoming,
        )

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

    def complete_task(self, task: CareTask) -> "CareTask | None":
        """Mark a task complete; auto-create its next occurrence on the owning pet.

        For daily/weekly tasks, a fresh instance dated for the next occurrence is
        added to whichever pet owns the task. Returns that new task (or None for
        one-off tasks, which do not repeat).
        """
        task.mark_complete()
        upcoming = task.next_occurrence()
        if upcoming is not None:
            for pet in self.owner.pets:
                if task in pet.tasks:
                    pet.add_task(upcoming)
                    break
        return upcoming

    def detect_conflicts(self) -> list[str]:
        """Return warning messages for tasks scheduled at the same preferred_time.

        Lightweight check: pending tasks (across all pets) that share the same
        clock time are flagged, whether they belong to the same pet or different
        ones. Returns a list of warning strings and never raises, so the caller
        can print warnings without crashing the program. No timed conflicts
        returns an empty list.
        """
        by_time: dict[str, list[str]] = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.completed or not task.preferred_time:
                    continue  # done or untimed tasks can't conflict
                by_time.setdefault(task.preferred_time, []).append(
                    f"{task.title} ({pet.name})"
                )

        warnings: list[str] = []
        for time_str in sorted(by_time):
            labels = by_time[time_str]
            if len(labels) > 1:
                warnings.append(
                    f"Conflict at {time_str}: "
                    + ", ".join(labels)
                    + " are scheduled at the same time."
                )
        return warnings

    def _all_tasks(self) -> list[CareTask]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.owner.pets for task in pet.tasks]

    @staticmethod
    def _time_key(time_str: str | None) -> tuple[int, int]:
        """Turn a 'HH:MM' string into a sortable (bucket, minutes) key; untimed last."""
        if not time_str:
            return (1, 0)  # tasks with no preferred_time sort after timed ones
        hours, minutes = time_str.split(":")
        return (0, int(hours) * 60 + int(minutes))

    def sort_by_time(self, tasks: list[CareTask] | None = None) -> list[CareTask]:
        """Return tasks sorted by their preferred_time ('HH:MM'); untimed tasks last."""
        if tasks is None:
            tasks = self._all_tasks()
        return sorted(tasks, key=lambda t: self._time_key(t.preferred_time))

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[CareTask]:
        """Return tasks across pets, optionally filtered by completion and/or pet name."""
        results: list[CareTask] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results


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
