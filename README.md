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

- **`Task`**: one care activity (title, duration, priority, frequency, completion status). `edit()` updates it, and `mark_complete()` marks it done.
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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
