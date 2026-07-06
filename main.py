"""PawPal+ demo script (temporary testing ground).

Runs the logic layer in the terminal to verify it works end to end, including
the Phase 4 sorting and filtering methods on the Scheduler.

Run with:  python main.py
"""

from datetime import date

from pawpal_system import CareTask, Pet, Owner, Scheduler


def show(title, tasks):
    """Print a labeled list of tasks."""
    print(f"\n{title}")
    print("-" * len(title))
    if not tasks:
        print("  (none)")
    for task in tasks:
        when = task.preferred_time or "--:--"
        print(f"  {when}  {task}")


def main() -> None:
    # --- Pets with tasks added intentionally OUT OF ORDER by time -----
    mochi = Pet("Mochi", "cat")
    mochi.add_task(CareTask("Grooming", 25, "low", preferred_time="14:00"))
    mochi.add_task(CareTask("Feeding", 10, "high", preferred_time="07:30"))
    mochi.add_task(CareTask("Litter box", 5, "medium", preferred_time="12:00"))

    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(CareTask("Evening walk", 30, "high", preferred_time="18:00"))
    biscuit.add_task(CareTask("Meds", 5, "high", preferred_time="08:00"))
    biscuit.add_task(CareTask("Fetch / play", 20, "low", preferred_time="16:30"))

    # Mark one task complete so the completion filter has something to show.
    biscuit.tasks[1].mark_complete()  # Meds done

    owner = Owner("Jordan", available_minutes=75)
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    scheduler = Scheduler(owner, day="2026-07-06")

    print(f"Today's tasks for {owner.name} ({len(owner.pets)} pets)")
    print("=" * 60)

    # --- Sorting: tasks were added out of order; sort them by time ----
    show("All tasks sorted by time (sort_by_time):", scheduler.sort_by_time())

    # --- Filtering: by completion status ------------------------------
    show("Filter: only completed tasks:", scheduler.filter_tasks(completed=True))
    show("Filter: only incomplete tasks:", scheduler.filter_tasks(completed=False))

    # --- Filtering: by pet name ---------------------------------------
    show("Filter: only Mochi's tasks:", scheduler.filter_tasks(pet_name="Mochi"))

    # --- Combined: sort Biscuit's tasks by time -----------------------
    biscuit_by_time = scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Biscuit"))
    show("Biscuit's tasks, sorted by time:", biscuit_by_time)

    # --- Recurring tasks: completing one spawns the next occurrence ---
    print("\n\nRecurring tasks demo")
    print("=" * 60)

    daily_feed = CareTask("Feeding", 10, "high", recurrence="daily",
                          due_date=date(2026, 7, 6))
    weekly_bath = CareTask("Bath", 40, "medium", recurrence="weekly",
                           due_date=date(2026, 7, 6))
    one_off_vet = CareTask("Vet visit", 60, "high", recurrence="once",
                           due_date=date(2026, 7, 6))
    rex = Pet("Rex", "dog")
    for t in (daily_feed, weekly_bath, one_off_vet):
        rex.add_task(t)
    owner.add_pet(rex)

    print(f"\nRex starts with {len(rex.tasks)} tasks (all due 2026-07-06).")

    for task in (daily_feed, weekly_bath, one_off_vet):
        nxt = scheduler.complete_task(task)
        if nxt is None:
            print(f"  Completed '{task.title}' ({task.recurrence}) -> no next occurrence.")
        else:
            print(f"  Completed '{task.title}' ({task.recurrence}) -> "
                  f"next occurrence due {nxt.due_date}.")

    print(f"\nRex now has {len(rex.tasks)} tasks "
          f"(2 recurring ones respawned, vet visit did not):")
    for t in rex.tasks:
        status = "done" if t.completed else "pending"
        print(f"  {t.title:12} {t.recurrence:7} due {t.due_date}  [{status}]")

    # --- Conflict detection: two tasks scheduled at the same time -----
    print("\n\nConflict detection demo")
    print("=" * 60)
    # Mochi already has "Feeding" at 07:30. Add another task at 07:30 for the
    # SAME pet, and one at 07:30 for a DIFFERENT pet, to trigger a conflict.
    mochi.add_task(CareTask("Playtime", 15, "low", preferred_time="07:30"))
    biscuit.add_task(CareTask("Backyard", 20, "low", preferred_time="07:30"))

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print(f"Found {len(conflicts)} conflict(s):")
        for warning in conflicts:
            print(f"  ! {warning}")
    else:
        print("No conflicts found.")


if __name__ == "__main__":
    main()
