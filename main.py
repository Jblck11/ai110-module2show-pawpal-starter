"""PawPal+ demo script (temporary testing ground).

Runs the logic layer in the terminal to verify it works end to end:
build an owner with a couple of pets, give them tasks, then print the
schedule the Scheduler produces for today.

Run with:  python main.py
"""

from pawpal_system import CareTask, Pet, Owner, Scheduler


def main() -> None:
    # --- Pets and their care tasks ------------------------------------
    mochi = Pet("Mochi", "cat")
    mochi.add_task(CareTask("Feeding", duration_minutes=10, priority="high"))
    mochi.add_task(CareTask("Litter box", duration_minutes=5, priority="medium"))
    mochi.add_task(CareTask("Grooming", duration_minutes=25, priority="low"))

    biscuit = Pet("Biscuit", "dog")
    biscuit.add_task(CareTask("Morning walk", duration_minutes=30, priority="high"))
    biscuit.add_task(CareTask("Meds", duration_minutes=5, priority="high"))
    biscuit.add_task(CareTask("Fetch / play", duration_minutes=20, priority="low"))

    # --- Owner and their daily time budget ----------------------------
    jordan = Owner("Jordan", available_minutes=75)
    jordan.add_pet(mochi)
    jordan.add_pet(biscuit)

    # --- Build and print today's schedule -----------------------------
    scheduler = Scheduler(jordan, day="2026-07-05")
    plan = scheduler.build_plan()

    print(f"Today's Schedule for {jordan.name} "
          f"({len(jordan.pets)} pets, {jordan.available_minutes} min available)")
    print("=" * 60)
    print(plan.explain())
    print("-" * 60)
    print(f"Total scheduled time: {plan.total_time()} min")
    print(f"Skipped {len(plan.skipped)} task(s) that didn't fit.")


if __name__ == "__main__":
    main()
