"""PawPal+ logic layer: backend classes for pet care planning.

Classes follow diagrams/uml_draft.mmd. Scheduler methods are still stubs.
"""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import combinations
from typing import List, Optional, Tuple


@dataclass
class Task:
    """A single pet care task (e.g., walk, feeding, grooming)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    frequency: str = "daily"  # "daily" | "weekly" | "once"
    completed: bool = False
    time: str = ""  # preferred start as "HH:MM" (e.g., "07:30"); "" means any time
    due_date: date = field(default_factory=date.today)

    def edit(self, duration_minutes: int, priority: str) -> None:
        """Update this task's duration and priority."""
        self.duration_minutes = duration_minutes
        self.priority = priority

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def minutes_after_midnight(self) -> int:
        """Convert this task's "HH:MM" time to minutes after midnight.

        Example: "07:30" -> 450. Parsing uses datetime.strptime, so impossible
        clock values are rejected rather than silently accepted.

        Returns:
            The task's start time as whole minutes after midnight (0-1439).

        Raises:
            ValueError: If the time is malformed or impossible, e.g. "7pm" or "25:00".
        """
        parsed = datetime.strptime(self.time, "%H:%M")
        return parsed.hour * 60 + parsed.minute

    def next_occurrence(self) -> Optional["Task"]:
        """Build the next instance of a recurring task.

        The copy keeps every field (title, duration, priority, time) but is marked
        incomplete and has its due date moved forward: +1 day for "daily",
        +7 days for "weekly". timedelta handles month and year rollover, so
        Dec 31 + 1 day is Jan 1.

        Returns:
            A new Task due on the next date, or None if frequency is "once"
            (or any value other than "daily"/"weekly").
        """
        intervals = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        if self.frequency not in intervals:
            return None
        return replace(self, completed=False, due_date=self.due_date + intervals[self.frequency])


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        self.tasks = [t for t in self.tasks if t.title != title]


@dataclass
class Owner:
    """A pet owner with a daily time budget and preferences."""

    name: str
    available_minutes: int
    day_start_minute: int = 8 * 60  # minutes after midnight (8 * 60 = 08:00)
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every (pet, task) pair across all of this owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledTask:
    """A task placed at a specific time in the daily plan."""

    task: Task
    pet: Pet
    start_minute: int  # minutes after midnight (e.g., 480 = 08:00)

    @property
    def end_minute(self) -> int:
        """Minute of the day when this task finishes."""
        return self.start_minute + self.task.duration_minutes

    def start_time(self) -> str:
        """Return the start as a clock string, e.g. 480 -> "08:00"."""
        hours, minutes = divmod(self.start_minute, 60)
        return f"{hours:02d}:{minutes:02d}"


class Scheduler:
    """Builds and explains a daily care plan from an owner's constraints and a pet's tasks."""

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """Mark a pet's task complete and queue its next occurrence if it recurs.

        Use this instead of Task.mark_complete() when recurring tasks should
        regenerate themselves automatically.

        Args:
            pet: The pet that owns the task; the next occurrence is added to it.
            task: The task being completed.

        Completing a task that is already done does nothing, so a double click
        can't queue a duplicate next occurrence.

        Returns:
            The newly created next-occurrence Task, or None if the task doesn't
            repeat or was already completed.
        """
        if task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def detect_conflicts(self, owner: Owner) -> List[str]:
        """Find tasks whose time windows overlap and describe each clash.

        Two incomplete tasks conflict when they share a due date and their windows
        overlap (a.start < b.end and b.start < a.end), whether they belong to the
        same pet or different pets. Back-to-back tasks (one ends as the next starts)
        are not conflicts. Every pair is checked with itertools.combinations, which
        is O(n^2) but clear and fast enough for a day's worth of pet tasks.

        Completed tasks and tasks with no set time are skipped. A malformed time is
        reported as a warning instead of raising, so the program never crashes here.

        Args:
            owner: The owner whose pets' tasks are checked.

        Returns:
            Human-readable warning strings, one per invalid time or overlapping pair;
            an empty list means no conflicts.
        """
        warnings: List[str] = []
        timed: List[ScheduledTask] = []
        for pet, task in owner.get_all_tasks():
            if task.completed or not task.time:
                continue
            try:
                timed.append(ScheduledTask(task, pet, task.minutes_after_midnight()))
            except ValueError:
                warnings.append(f"WARNING: {pet.name}'s '{task.title}' has an invalid time '{task.time}'.")

        # Compare every pair once; with a day's worth of pet tasks this is plenty fast.
        for a, b in combinations(timed, 2):
            same_day = a.task.due_date == b.task.due_date
            overlaps = a.start_minute < b.end_minute and b.start_minute < a.end_minute
            if same_day and overlaps:
                who = a.pet.name if a.pet is b.pet else f"{a.pet.name} and {b.pet.name}"
                warnings.append(
                    f"WARNING: {who} - '{a.task.title}' ({a.task.time}) overlaps "
                    f"'{b.task.title}' ({b.task.time}) on {a.task.due_date}."
                )
        return warnings

    def sort_by_time(self, tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Order (pet, task) pairs chronologically.

        Sorts by due date, then by start time in minutes after midnight, so "7:30"
        and "07:30" sort the same (comparing the raw text would put "7:30" after
        "18:00"). Within each day, tasks with no set time or an invalid time go
        last, in their original order.

        Args:
            tasks: (pet, task) pairs, e.g. from Owner.get_all_tasks() or filter_tasks().

        Returns:
            A new sorted list; the input list is not modified.
        """

        def sort_key(pair: Tuple[Pet, Task]) -> Tuple[date, bool, int]:
            task = pair[1]
            try:
                return (task.due_date, False, task.minutes_after_midnight())
            except ValueError:  # no time set ("") or malformed
                return (task.due_date, True, 0)

        return sorted(tasks, key=sort_key)

    def filter_tasks(
        self,
        owner: Owner,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Select the owner's tasks by pet name and/or completion status.

        Filters combine with AND; leaving one as None means "don't filter on that".

        Args:
            owner: The owner whose pets' tasks are searched.
            pet_name: Only include this pet's tasks (case-insensitive), or None for all pets.
            completed: True for done tasks, False for unfinished ones, or None for both.

        Returns:
            The matching (pet, task) pairs, in the owner's original task order.
        """
        return [
            (pet, task)
            for pet, task in owner.get_all_tasks()
            if (pet_name is None or pet.name.lower() == pet_name.lower())
            and (completed is None or task.completed == completed)
        ]

    def generate_plan(self, owner: Owner, pet: Pet) -> List[ScheduledTask]:
        """Choose, order, and time-slot tasks that fit the owner's available time."""
        pass

    def explain_plan(self, plan: List[ScheduledTask]) -> str:
        """Return a human-readable explanation of why each task was chosen and when."""
        pass