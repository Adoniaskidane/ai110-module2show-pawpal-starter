"""Tests for the PawPal+ logic layer."""

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Leo", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10, "high"))

    assert len(pet.tasks) == 1
