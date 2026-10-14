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
