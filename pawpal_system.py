"""PawPal+ logic layer: backend classes for pet care planning.

Classes follow diagrams/uml_final.mmd. Scheduler.generate_plan() and explain_plan() are still stubs.
Owner.save_to_json() / Owner.load_from_json() persist everything to data.json between runs.
"""

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

DATA_FILE = "data.json"
SCHEMA_VERSION = 1  # bump when the saved JSON layout changes


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert this task to JSON-safe data; due_date becomes an ISO string like "2026-10-19"."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Rebuild a Task from to_dict() output.

        Missing optional fields fall back to their defaults and unknown keys are
        ignored, so older or newer data files still load.

        Raises:
            KeyError: If a required field (title, duration_minutes, priority) is missing.
            ValueError: If due_date isn't an ISO date or duration isn't a number.
        """
        return cls(
            title=str(data["title"]),
            duration_minutes=int(data["duration_minutes"]),
            priority=str(data["priority"]),
            frequency=str(data.get("frequency", "daily")),
            completed=bool(data.get("completed", False)),
            time=str(data.get("time", "")),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else date.today(),
        )


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert this pet and its tasks to JSON-safe data."""
        return {"name": self.name, "species": self.species, "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pet":
        """Rebuild a Pet (and its tasks) from to_dict() output."""
        return cls(
            name=str(data["name"]),
            species=str(data.get("species", "other")),
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
        )


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert this owner, their pets, and every task to JSON-safe data."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "day_start_minute": self.day_start_minute,
            "preferences": list(self.preferences),
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Owner":
        """Rebuild an Owner (with pets and tasks) from to_dict() output."""
        return cls(
            name=str(data["name"]),
            available_minutes=int(data["available_minutes"]),
            day_start_minute=int(data.get("day_start_minute", 8 * 60)),
            preferences=[str(p) for p in data.get("preferences", [])],
            pets=[Pet.from_dict(p) for p in data.get("pets", [])],
        )

    def save_to_json(self, path: Union[str, Path] = DATA_FILE) -> None:
        """Save this owner, their pets, and all tasks to a JSON file.

        The file is written atomically: data goes to a temporary file in the same
        folder, which then replaces the target in one step. If the program crashes
        mid-save, the previous data.json is left intact instead of half-written.

        Args:
            path: Where to write; defaults to "data.json" in the working directory.
        """
        path = Path(path)
        payload = {
            "version": SCHEMA_VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "owner": self.to_dict(),
        }
        fd, tmp_name = tempfile.mkstemp(dir=path.parent or ".", prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(payload, tmp, indent=2)
            os.replace(tmp_name, path)
        except BaseException:
            os.unlink(tmp_name)
            raise

    @classmethod
    def load_from_json(cls, path: Union[str, Path] = DATA_FILE) -> Optional["Owner"]:
        """Load an owner saved by save_to_json().

        Args:
            path: The JSON file to read; defaults to "data.json".

        Returns:
            The restored Owner, or None if the file doesn't exist yet (first run).

        Raises:
            ValueError: If the file isn't valid PawPal+ data (bad JSON, missing
                fields, wrong types) or was saved by a newer schema version.
        """
        path = Path(path)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            version = payload.get("version", 1)
            if version > SCHEMA_VERSION:
                raise ValueError(f"{path} uses data version {version}; this PawPal+ supports up to {SCHEMA_VERSION}.")
            return cls.from_dict(payload["owner"])
        except ValueError:
            raise  # includes json.JSONDecodeError and bad dates/numbers
        except (KeyError, TypeError, AttributeError) as err:
            raise ValueError(f"{path} is not valid PawPal+ data: {err!r}") from err


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