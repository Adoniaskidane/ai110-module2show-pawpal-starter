"""PawPal+ logic layer: backend classes for pet care planning.

Skeleton generated from diagrams/uml_draft.mmd. Method bodies are stubs.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    """A single pet care task (e.g., walk, feeding, grooming)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"

    def edit(self, duration_minutes: int, priority: str) -> None:
        """Update this task's duration and priority."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass


@dataclass
class Owner:
    """A pet owner with a daily time budget and preferences."""

    name: str
    available_minutes: int
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        pass


class Scheduler:
    """Builds and explains a daily care plan from an owner's constraints and a pet's tasks."""

    def generate_plan(self, owner: Owner, pet: Pet) -> List[Task]:
        """Choose and order tasks that fit the owner's available time and preferences."""
        pass

    def explain_plan(self, plan: List[Task]) -> str:
        """Return a human-readable explanation of why each task was chosen and when."""
        pass
