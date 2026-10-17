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

## 🧩 Implementation Summary

The logic layer lives in `pawpal_system.py` and is built from five classes:

- **`Task`**: one care activity (title, duration, priority, frequency, completion status, optional `HH:MM` time, due date). `edit()` updates it, and `mark_complete()` marks it done.
- **`Pet`**: a pet (name, species) that owns its list of tasks through `add_task()` and `remove_task()`.
- **`Owner`**: the person doing the care. Stores their daily time budget, day start time, preferences, and pets. `get_all_tasks()` returns every `(pet, task)` pair across all pets, which is the single entry point for multi-pet data.
- **`ScheduledTask`**: a task placed at a specific start minute for a specific pet, with `end_minute` and `start_time()` for display.
- **`Scheduler`**: the planner. `generate_plan()` will turn the owner's tasks into a list of `ScheduledTask`s, and `explain_plan()` will describe why each was chosen. These two methods are not implemented yet.

**How they work together:** an `Owner` holds `Pet`s, each `Pet` holds `Task`s, and code that needs every task asks the owner via `get_all_tasks()` instead of reaching into individual pets. Times are stored as minutes after midnight so tasks can be placed back to back with simple addition, then formatted as `HH:MM` only for display.

`main.py` is a temporary demo that builds an owner with two pets and prints today's schedule. Until `Scheduler` is implemented, it uses a small helper that lists tasks back to back from the owner's day start (no sorting or time-budget check yet). `tests/test_pawpal.py` covers task completion and adding tasks to a pet.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...

ai110-module2show-pawpal-starter$ python3 main.py
Today's Schedule for Jhon
========================================
08:00  Leo      Morning walk (30 min) [priority: high]
08:30  Leo      Feeding (10 min) [priority: high]
08:40  Milo     Litter box cleanup (15 min) [priority: medium]
08:55  Milo     Brushing (20 min) [priority: low]

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

Beyond storing tasks, the `Scheduler` in `pawpal_system.py` can sort, filter, check for time conflicts, and handle recurring tasks. Run `python main.py` to see each feature in action.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | By due date, then `HH:MM` time; tasks with no set time go last each day |
| Filtering | `Scheduler.filter_tasks()` | By pet name, completion status, or both |
| Conflict handling | `Scheduler.detect_conflicts()`, `Task.minutes_after_midnight()` | Flags overlapping time windows (same or different pets) as warnings, never crashes |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a daily/weekly task automatically creates the next one |

### Sorting: `Scheduler.sort_by_time(tasks)`

Takes a list of `(pet, task)` pairs and returns a new list in chronological order: first by `due_date`, then by the task's `time` (`"HH:MM"`). It uses `sorted()` with a lambda key:

```python
sorted(tasks, key=lambda pair: (pair[1].due_date, pair[1].time == "", pair[1].time))
```

- Zero-padded `"HH:MM"` strings sort correctly as plain text (`"07:30" < "18:00"`), so no conversion is needed.
- `time == ""` is `False` for timed tasks and `True` for untimed ones; since `False` sorts first, tasks with no set time land at the end of each day.
- The input list is not modified.

### Filtering: `Scheduler.filter_tasks(owner, pet_name=None, completed=None)`

Returns the owner's `(pet, task)` pairs that match the given filters.

- `pet_name="Milo"` keeps only Milo's tasks (case-insensitive).
- `completed=False` keeps unfinished tasks; `completed=True` keeps finished ones.
- Both filters can be combined, and leaving one as `None` means "don't filter on that".
- The output can be passed straight into `sort_by_time()`, e.g. "today's unfinished tasks in time order".

### Conflict detection: `Scheduler.detect_conflicts(owner)`

Returns a list of warning strings (empty if there are no problems) instead of raising, so a bad schedule never crashes the app.

- Two incomplete tasks conflict when they share a due date **and** their time windows overlap: `a.start < b.end and b.start < a.end`. This catches partial overlaps (a 30-minute walk at 07:00 clashes with a task at 07:15), not just identical start times.
- Works for the same pet (`Leo - 'Morning walk' overlaps 'Medication'`) and across pets (`Leo and Milo - 'Vet call' overlaps 'Feeding'`).
- Back-to-back tasks (one ends exactly when the next starts) are not conflicts.
- Times are parsed by `Task.minutes_after_midnight()`, which uses `datetime.strptime(..., "%H:%M")`. Invalid times like `"7pm"` or `"25:00"` produce a warning and are skipped.
- Completed tasks and tasks with no set time are ignored.
- Every pair is compared with `itertools.combinations`. This is O(n²), chosen on purpose for readability; a day's worth of pet tasks is small enough that it runs instantly (see the tradeoff in `reflection.md`).

### Recurring tasks: `Scheduler.mark_task_complete(pet, task)`

Marks a task done and, if it repeats, adds its next occurrence to the pet.

- `Task.next_occurrence()` builds the copy with `dataclasses.replace`, keeping the title, duration, priority, and time but resetting `completed` to `False`.
- The new due date is calculated with `timedelta`: `+ timedelta(days=1)` for `"daily"`, `+ timedelta(weeks=1)` for `"weekly"`. `timedelta` handles month and year rollover (Dec 31 → Jan 1).
- `"once"` tasks are just marked complete; no new task is created and the method returns `None`.
- Calling `Task.mark_complete()` directly still only marks the task done, without creating a next occurrence.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
