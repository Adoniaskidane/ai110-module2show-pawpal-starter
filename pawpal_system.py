"""PawPal+ logic layer: backend classes for pet care planning.

Classes follow diagrams/uml_draft.mmd. Scheduler methods are still stubs.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Task:
    """A single pet care task (e.g., walk, feeding, grooming)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    frequency: str = "daily"  # "daily" | "weekly" | "once"
    completed: bool = False

    def edit(self, duration_minutes: int, priority: str) -> None:
        """Update this task's duration and priority."""
        self.duration_minutes = duration_minutes
        self.priority = priority

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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

    def generate_plan(self, owner: Owner, pet: Pet) -> List[ScheduledTask]:
        """Choose, order, and time-slot tasks that fit the owner's available time."""
        pass

    def explain_plan(self, plan: List[ScheduledTask]) -> str:
        """Return a human-readable explanation of why each task was chosen and when."""
        pass
