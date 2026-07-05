# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design breaks PawPal+ into five classes that follow the natural flow of
the scenario: capture tasks → apply the owner's constraints → produce an explained plan.
The data classes (`Owner`, `Pet`, `CareTask`) hold information, while `Scheduler` and
`DailyPlan` separate the *logic* of building a plan from the *result* it produces. I kept
the scheduling algorithm out of the plan object on purpose so I can test the logic without
touching any display code.

The five classes and their responsibilities:

- **`CareTask`** — Represents one unit of pet care (walk, feeding, meds, grooming). Holds
  its `title`, `duration_minutes`, `priority`, optional `preferred_time`, `recurrence`, and
  `category`. It knows how to score its own priority (`priority_score()`) and whether it is
  due on a given day (`is_due_today()`).

- **`Pet`** — Represents the animal the tasks belong to. Holds a `name`, `species`, and its
  list of `CareTask`s. Responsible for managing its own tasks (`add_task`, `remove_task`) and
  reporting which tasks are due today (`tasks_due`).

- **`Owner`** — Represents the user and their constraints. Holds the owner's `name`, their
  `pets`, the `available_minutes` for the day, and a `preferences` dictionary. Responsible for
  gathering all tasks due across every pet (`all_tasks_due`).

- **`Scheduler`** — The "brain" of the system. Takes an `Owner` and a `day`, then builds the
  plan (`build_plan`) by sorting tasks on priority (`_sort_tasks`) and fitting them into the
  available time (`_fits`). This is where the constraint logic lives.

- **`DailyPlan`** — The output. Holds the `scheduled` tasks, the `skipped` tasks, and the
  `reasons` for each decision. Responsible for explaining the plan (`explain`), rendering it
  for the UI (`to_table`), and reporting total time (`total_time`) — this covers the
  "explain why it chose that plan" requirement.

Relationships: an `Owner` *has* many `Pet`s, and a `Pet` *has* many `CareTask`s
(aggregation). The `Scheduler` reads an `Owner` and *produces* a `DailyPlan`.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
