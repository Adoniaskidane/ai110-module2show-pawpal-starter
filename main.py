"""Temporary testing ground: build sample data and print today's schedule."""

from pawpal_system import Owner, Pet, ScheduledTask, Task


def build_schedule(owner: Owner) -> list[ScheduledTask]:
    """Place every pet's tasks back to back from the owner's day start.

    Stand-in until Scheduler.generate_plan is implemented.
    """
    schedule = []
    current = owner.day_start_minute
    for pet, task in owner.get_all_tasks():
        schedule.append(ScheduledTask(task=task, pet=pet, start_minute=current))
        current += task.duration_minutes
    return schedule


def main() -> None:
    owner = Owner(name="Jhon", available_minutes=120)

    Leo = Pet(name="Leo", species="dog")
    Leo.add_task(Task("Morning walk", 30, "high"))
    Leo.add_task(Task("Feeding", 10, "high"))

    Milo = Pet(name="Milo", species="cat")
    Milo.add_task(Task("Litter box cleanup", 15, "medium"))
    Milo.add_task(Task("Brushing", 20, "low", frequency="weekly"))

    owner.add_pet(Leo)
    owner.add_pet(Milo)

    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)
    for item in build_schedule(owner):
        print(
            f"{item.start_time()}  {item.pet.name:<8} {item.task.title} "
            f"({item.task.duration_minutes} min) [priority: {item.task.priority}]"
        )


if __name__ == "__main__":
    main()
