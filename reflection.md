# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design has four classes. Three of them hold data: `Owner`, `Pet`, and `Task`. The fourth, `Scheduler`, holds the planning logic. An owner has one or more pets, and each pet owns its own list of care tasks. The `Scheduler` depends on `Owner` and `Pet` but does not store them. It reads them when it builds a plan. I kept the data separate from the scheduling logic so that the scheduling rules can change without touching how pets and tasks are stored.

- **Task**: represents one pet care activity, such as a walk, feeding, or grooming. It stores a `title`, a `duration_minutes`, and a `priority` (low, medium, or high). Its `edit()` method lets the duration and priority be changed after the task is created.
- **Pet**: represents a single animal (`name`, `species`) and manages the care tasks it needs. `add_task()` and `remove_task()` keep the task list up to date. Pet and Task use composition, so a task belongs to exactly one pet.
- **Owner**: represents the person doing the care. It stores how much time they have in a day (`available_minutes`) and their `preferences`, and it keeps track of their pets through `add_pet()`. The owner provides the main constraints the scheduler has to respect.
- **Scheduler**: takes an owner and a pet and produces the daily plan. `generate_plan()` picks and orders the tasks that fit within the owner's available time, putting higher-priority tasks and the owner's preferences first. `explain_plan()` returns a readable explanation of why each task was included, so the user can understand and trust the plan.

**b. Design changes**

Yes. When I reviewed the skeleton, I found a gap in my first design. `generate_plan()` returned a plain `List[Task]`, but a `Task` only has a title, duration, and priority. It has no idea *when* it happens. That meant the scheduler could choose and order tasks but couldn't produce a real daily plan like "08:00 — Morning walk (30 min)", even though showing when each task happens is one of the project requirements.

To fix this, I added a new `ScheduledTask` class that wraps a `Task` and records the `Pet` it belongs to plus a `start_minute` (minutes after midnight, so 480 means 08:00). It also provides an `end_minute` and a `start_time()` method that turns the number into a clock string for display. I also gave `Owner` a `day_start_minute` field (default 08:00) so the scheduler knows where the day begins. Now `generate_plan()` returns `List[ScheduledTask]`, and `explain_plan()` takes that list.

I chose to store times as whole minutes instead of strings like "08:00" because it keeps the scheduling math simple: each task can start at the previous task's `end_minute`, and I only format the time when it is shown to the user. I also kept `Task` unchanged, because a task describes *what* needs to happen, while `ScheduledTask` describes *when* it happens in a specific plan. Keeping those separate means the same task can appear at a different time on a different day without editing the task itself. I updated the UML diagram to include the new class and its relationships so it still matches the code.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

My conflict detection (`Scheduler.detect_conflicts()`) chooses readability over speed. It checks every pair of timed tasks with `itertools.combinations` and flags two tasks if they fall on the same day and their time windows overlap (`a.start < b.end and b.start < a.end`). That is O(n²) comparisons. An earlier version sorted the tasks by start time first and stopped comparing as soon as the next task started after the current one ended. That version is faster (roughly O(n log n)), but it only works because of the sort, and the early `break` is easy to misread or break by accident when editing the code later.

This tradeoff is reasonable because a pet owner only has a handful of tasks per day. Even with 20 tasks, the pairwise check makes only 190 comparisons, which runs instantly. At that size the speed difference doesn't matter, but readable code does. Anyone can look at the overlap check and see what "conflict" means without having to reason about sort order. If PawPal+ ever had to schedule hundreds of tasks (for example, a boarding kennel), I would switch back to the sorted approach.

A related choice was to check for overlapping durations rather than only exact matching start times. A 07:00 walk that lasts 30 minutes does conflict with a 07:15 task, so checking only exact start times would miss real clashes. The cost is that tasks with no set time are skipped entirely, so the scheduler can't warn about them.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code as a reviewer and a pair programmer. First, I pasted the assignment's requirements for the logic layer and asked whether my skeleton was on track. It compared my code to the spec and pointed out three gaps. `Task` was missing frequency and completion status, `Owner` had no `get_all_tasks()` method, and `Scheduler.generate_plan()` read tasks from a single pet instead of from the owner. It also suggested that `get_all_tasks()` return `(pet, task)` pairs instead of a flat list of tasks, because `ScheduledTask` needs to know which pet each task belongs to. After that, I used it to sync the UML diagram with the code, create `main.py` as a testing script, and draft my first two pytest tests.

The most helpful prompts were the ones where I gave it the exact requirement text and asked "am I on the right track, did I miss anything?" That gave me a specific checklist tied to the spec instead of general advice.

**b. Judgment and verification**

I did not accept all of the AI's suggestions at once. It recommended three changes, and I only told it to apply the first two (the new `Task` fields and `Owner.get_all_tasks()`). I held off on changing `generate_plan()` to take only the owner. <!-- Add your reason here, e.g. you wanted to write the scheduling logic yourself. --> Because of that, the AI did not invent a scheduler when it wrote `main.py`. It used a small, clearly labeled stand-in helper and told me the output was not coming from my `Scheduler` yet. I also changed the sample owner and pet names in `main.py` to my own.

To verify the results, I ran `python main.py` and checked that the schedule included tasks from both pets with times that did not overlap. I also ran `python -m pytest` and confirmed that both tests passed. I reviewed the UML diff to make sure the diagram matched the code and did not show a design I had not built yet.

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
