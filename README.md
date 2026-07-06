# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output from running `python main.py` — evidence the logic layer runs correctly:

```
Today's Schedule for Jordan (2 pets, 75 min available)
============================================================
08:00 — Meds: Placed at 08:00: high priority, fits in the 75 min still available.
08:05 — Feeding: Placed at 08:05: high priority, fits in the 70 min still available.
08:15 — Morning walk: Placed at 08:15: high priority, fits in the 60 min still available.
08:45 — Litter box: Placed at 08:45: medium priority, fits in the 30 min still available.
08:50 — Fetch / play: Placed at 08:50: low priority, fits in the 25 min still available.
(skipped) Grooming: Skipped: needs 25 min but only 5 min left in the day.
------------------------------------------------------------
Total scheduled time: 70 min
Skipped 1 task(s) that didn't fit.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

These are the scheduling features implemented in the logic layer (`pawpal_system.py`),
each with the method that implements it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Priority scheduling | `Scheduler.build_plan()`, `Scheduler._sort_tasks()` | Sorts tasks by priority (high → low), packs them into the owner's `available_minutes`, and skips any that don't fit. |
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks by their `preferred_time` ("HH:MM"). Uses a lambda key that converts each time to total minutes; untimed tasks sort last. |
| Filtering | `Scheduler.filter_tasks(completed=..., pet_name=...)` | Returns tasks across all pets, optionally filtered by completion status and/or pet name. Both filters are optional and combinable. |
| Conflict detection | `Scheduler.detect_conflicts()` | Lightweight check that flags tasks sharing the same start time (same pet or different pets). Returns a list of warning strings and never raises. Detects exact-time clashes, not duration overlaps. |
| Recurring tasks | `Scheduler.complete_task()`, `CareTask.next_occurrence()`, `CareTask.next_due_date()` | Completing a daily/weekly task auto-creates a fresh instance for the next occurrence (daily → +1 day, weekly → +7 days via `timedelta`). One-off ("once") tasks do not repeat. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
