"""Tests for the PawPal+ logic layer.

Covers the core scheduling behaviors (sorting, filtering, recurrence, conflict
detection, and budget-aware planning) plus the important edge cases: a pet with
no tasks, untimed tasks, and two tasks at the exact same time.
"""

from datetime import date

from pawpal_system import CareTask, Pet, Owner, Scheduler


# --- Helpers ---------------------------------------------------------------

def make_scheduler(pets, available_minutes=120):
    """Build an Owner with the given pets and return a Scheduler for them."""
    owner = Owner("Jordan", available_minutes=available_minutes)
    for pet in pets:
        owner.add_pet(pet)
    return Scheduler(owner, day="2026-07-06")


# --- Basics ----------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task's completed status to True."""
    task = CareTask("Morning walk", duration_minutes=20, priority="high")

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet("Mochi", "cat")

    assert len(pet.tasks) == 0  # starts with no tasks

    pet.add_task(CareTask("Feeding", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == 1


# --- Sorting correctness ---------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should return tasks ordered by preferred_time ('HH:MM')."""
    pet = Pet("Mochi", "cat")
    pet.add_task(CareTask("Grooming", 25, "low", preferred_time="14:00"))
    pet.add_task(CareTask("Feeding", 10, "high", preferred_time="07:30"))
    pet.add_task(CareTask("Litter box", 5, "medium", preferred_time="12:00"))
    scheduler = make_scheduler([pet])

    ordered = [t.preferred_time for t in scheduler.sort_by_time()]

    assert ordered == ["07:30", "12:00", "14:00"]


def test_sort_by_time_puts_untimed_tasks_last():
    """Tasks with no preferred_time should sort after all timed tasks."""
    pet = Pet("Mochi", "cat")
    pet.add_task(CareTask("Anytime play", 15, "low"))          # preferred_time=None
    pet.add_task(CareTask("Feeding", 10, "high", preferred_time="08:00"))
    scheduler = make_scheduler([pet])

    ordered = [t.title for t in scheduler.sort_by_time()]

    assert ordered == ["Feeding", "Anytime play"]


# --- Filtering -------------------------------------------------------------

def test_filter_tasks_by_pet_name():
    """filter_tasks(pet_name=...) should return only that pet's tasks."""
    mochi = Pet("Mochi", "cat")
    mochi.add_task(CareTask("Feeding", 10, "high"))
    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(CareTask("Walk", 30, "high"))
    scheduler = make_scheduler([mochi, biscuit])

    titles = [t.title for t in scheduler.filter_tasks(pet_name="Mochi")]

    assert titles == ["Feeding"]


def test_filter_tasks_by_completion_status():
    """filter_tasks(completed=True) should return only completed tasks."""
    pet = Pet("Mochi", "cat")
    done = CareTask("Feeding", 10, "high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(CareTask("Walk", 30, "high"))  # still incomplete
    scheduler = make_scheduler([pet])

    completed = scheduler.filter_tasks(completed=True)
    incomplete = scheduler.filter_tasks(completed=False)

    assert [t.title for t in completed] == ["Feeding"]
    assert [t.title for t in incomplete] == ["Walk"]


# --- Recurrence logic ------------------------------------------------------

def test_completing_daily_task_creates_task_for_next_day():
    """Completing a daily task should spawn a new task due the following day."""
    pet = Pet("Rex", "dog")
    daily = CareTask("Feeding", 10, "high", recurrence="daily",
                     due_date=date(2026, 7, 6))
    pet.add_task(daily)
    scheduler = make_scheduler([pet])

    new_task = scheduler.complete_task(daily)

    assert daily.completed is True
    assert new_task is not None
    assert new_task.due_date == date(2026, 7, 7)   # today + 1 day
    assert new_task.completed is False
    assert len(pet.tasks) == 2                     # original + next occurrence


def test_completing_weekly_task_creates_task_for_next_week():
    """Completing a weekly task should spawn a new task due seven days later."""
    pet = Pet("Rex", "dog")
    weekly = CareTask("Bath", 40, "medium", recurrence="weekly",
                      due_date=date(2026, 7, 6))
    pet.add_task(weekly)
    scheduler = make_scheduler([pet])

    new_task = scheduler.complete_task(weekly)

    assert new_task.due_date == date(2026, 7, 13)  # +7 days


def test_completing_once_task_creates_no_new_task():
    """A one-off ('once') task should not spawn a next occurrence."""
    pet = Pet("Rex", "dog")
    one_off = CareTask("Vet visit", 60, "high", recurrence="once",
                       due_date=date(2026, 7, 6))
    pet.add_task(one_off)
    scheduler = make_scheduler([pet])

    new_task = scheduler.complete_task(one_off)

    assert new_task is None
    assert len(pet.tasks) == 1  # nothing added


# --- Conflict detection ----------------------------------------------------

def test_detect_conflicts_flags_tasks_at_same_time():
    """Two tasks at the same preferred_time should produce a conflict warning."""
    mochi = Pet("Mochi", "cat")
    mochi.add_task(CareTask("Feeding", 10, "high", preferred_time="07:30"))
    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(CareTask("Walk", 30, "high", preferred_time="07:30"))
    scheduler = make_scheduler([mochi, biscuit])

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "07:30" in conflicts[0]


def test_detect_conflicts_none_when_times_unique():
    """Distinct times should produce no conflict warnings."""
    pet = Pet("Mochi", "cat")
    pet.add_task(CareTask("Feeding", 10, "high", preferred_time="07:30"))
    pet.add_task(CareTask("Walk", 30, "high", preferred_time="08:00"))
    scheduler = make_scheduler([pet])

    assert scheduler.detect_conflicts() == []


# --- Edge cases ------------------------------------------------------------

def test_build_plan_skips_tasks_over_budget():
    """A task that doesn't fit the remaining time should be skipped, not crammed in."""
    pet = Pet("Mochi", "cat")
    pet.add_task(CareTask("Quick feed", 10, "high"))
    pet.add_task(CareTask("Long groom", 30, "high"))
    scheduler = make_scheduler([pet], available_minutes=15)

    plan = scheduler.build_plan()

    scheduled_titles = [task.title for _, task in plan.scheduled]
    skipped_titles = [task.title for task in plan.skipped]
    assert scheduled_titles == ["Quick feed"]
    assert skipped_titles == ["Long groom"]


def test_pet_with_no_tasks_produces_empty_plan():
    """An owner whose pet has no tasks should get an empty, non-crashing plan."""
    pet = Pet("Mochi", "cat")  # no tasks
    scheduler = make_scheduler([pet])

    plan = scheduler.build_plan()

    assert plan.scheduled == []
    assert plan.skipped == []
    assert plan.total_time() == 0
