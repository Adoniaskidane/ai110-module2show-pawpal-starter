"""Command-line demo: build sample data and show each Scheduler feature."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_tasks(heading: str, pairs: list[tuple[Pet, Task]]) -> None:
    """Print a titled list of (pet, task) pairs."""
    print(f"\n{heading}")
    print("-" * 40)
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        status = "done" if task.completed else "todo"
        print(
            f"  {task.time or '--:--'}  {pet.name:<6} {task.title:<20} "
            f"due {task.due_date}  [{status}]"
        )


def main() -> None:
    owner = Owner(name="Jhon", available_minutes=120)

    # Tasks are added out of time order on purpose to exercise sort_by_time().
    Leo = Pet(name="Leo", species="dog")
    Leo.add_task(Task("Evening walk", 30, "high", time="18:00"))
    Leo.add_task(Task("Feeding", 10, "high", time="07:30"))
    Leo.add_task(Task("Morning walk", 30, "high", time="07:00"))

    Milo = Pet(name="Milo", species="cat")
    Milo.add_task(Task("Brushing", 20, "low", frequency="weekly"))  # no set time
    Milo.add_task(Task("Litter box cleanup", 15, "medium", time="12:15"))
    Milo.add_task(Task("Feeding", 5, "high", time="08:00"))

    # Deliberate clashes for detect_conflicts():
    Leo.add_task(Task("Medication", 5, "high", time="07:00"))  # same pet as Morning walk
    Leo.add_task(Task("Vet call", 20, "medium", time="08:00"))  # different pet: Milo's Feeding

    owner.add_pet(Leo)
    owner.add_pet(Milo)

    scheduler = Scheduler()

    # Completing recurring tasks automatically queues their next occurrence.
    scheduler.mark_task_complete(Leo, Leo.tasks[1])  # daily  -> due tomorrow
    scheduler.mark_task_complete(Milo, Milo.tasks[0])  # weekly -> due in 7 days

    print_tasks("All tasks (insertion order)", owner.get_all_tasks())
    print_tasks("All tasks sorted by time", scheduler.sort_by_time(owner.get_all_tasks()))
    print_tasks("Milo's tasks only", scheduler.filter_tasks(owner, pet_name="Milo"))
    print_tasks("Incomplete tasks, sorted", scheduler.sort_by_time(scheduler.filter_tasks(owner, completed=False)))
    print_tasks("Completed tasks", scheduler.filter_tasks(owner, completed=True))

    print("\nSchedule conflicts")
    print("-" * 40)
    for warning in scheduler.detect_conflicts(owner) or ["  No conflicts found."]:
        print(f"  {warning}")

    # Today's unfinished tasks in time order. Until Scheduler.generate_plan() exists,
    # this doesn't drop low-priority tasks to fit the owner's time budget.
    todays_tasks = [
        (pet, task)
        for pet, task in scheduler.filter_tasks(owner, completed=False)
        if task.due_date == date.today()
    ]
    print(f"\nToday's Schedule for {owner.name}")
    print("=" * 40)
    for pet, task in scheduler.sort_by_time(todays_tasks):
        print(
            f"{task.time or 'anytime':<7}  {pet.name:<6} {task.title} "
            f"({task.duration_minutes} min) [priority: {task.priority}]"
        )
    total = sum(task.duration_minutes for _, task in todays_tasks)
    print(f"Total: {total} of {owner.available_minutes} available minutes")

if __name__ == "__main__":
    main()
