"""Tests for the PawPal+ logic layer."""

import json
from datetime import date

import pytest

from pawpal_system import SCHEMA_VERSION, Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 18)


@pytest.fixture
def scheduler():
    return Scheduler()


def make_owner(*pets):
    owner = Owner(name="Sam", available_minutes=120)
    for pet in pets:
        owner.add_pet(pet)
    return owner


def titles(pairs):
    return [task.title for _, task in pairs]


# --- Task and Pet basics ---


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


def test_minutes_after_midnight_converts_clock_time():
    assert Task("Walk", 30, "high", time="00:00").minutes_after_midnight() == 0
    assert Task("Walk", 30, "high", time="07:30").minutes_after_midnight() == 450
    assert Task("Walk", 30, "high", time="23:59").minutes_after_midnight() == 1439


@pytest.mark.parametrize("bad_time", ["25:00", "7pm", "12:60", ""])
def test_minutes_after_midnight_rejects_invalid_time(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", 30, "high", time=bad_time).minutes_after_midnight()


# --- Sorting ---


def test_sort_by_time_returns_chronological_order(scheduler):
    pet = Pet("Mochi", "cat")
    for title, time in [("Dinner", "18:00"), ("Breakfast", "07:30"), ("Lunch", "12:00")]:
        pet.add_task(Task(title, 10, "medium", time=time, due_date=DAY))

    result = scheduler.sort_by_time(make_owner(pet).get_all_tasks())

    assert titles(result) == ["Breakfast", "Lunch", "Dinner"]


def test_sort_by_time_orders_by_date_before_time(scheduler):
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Tomorrow early", 10, "low", time="06:00", due_date=date(2026, 10, 19)))
    pet.add_task(Task("Today late", 10, "low", time="22:00", due_date=DAY))

    result = scheduler.sort_by_time(make_owner(pet).get_all_tasks())

    assert titles(result) == ["Today late", "Tomorrow early"]


def test_sort_by_time_puts_untimed_tasks_last_within_their_day(scheduler):
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Anytime today", 10, "low", due_date=DAY))
    pet.add_task(Task("Tomorrow walk", 10, "low", time="06:00", due_date=date(2026, 10, 19)))
    pet.add_task(Task("Today walk", 10, "low", time="09:00", due_date=DAY))

    result = scheduler.sort_by_time(make_owner(pet).get_all_tasks())

    assert titles(result) == ["Today walk", "Anytime today", "Tomorrow walk"]


def test_sort_by_time_keeps_input_order_for_identical_times(scheduler):
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("First", 10, "low", time="08:00", due_date=DAY))
    pet.add_task(Task("Second", 10, "low", time="08:00", due_date=DAY))

    result = scheduler.sort_by_time(make_owner(pet).get_all_tasks())

    assert titles(result) == ["First", "Second"]


def test_sort_by_time_does_not_modify_input(scheduler):
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Late", 10, "low", time="20:00", due_date=DAY))
    pet.add_task(Task("Early", 10, "low", time="06:00", due_date=DAY))
    pairs = make_owner(pet).get_all_tasks()

    scheduler.sort_by_time(pairs)

    assert titles(pairs) == ["Late", "Early"]


def test_sort_by_time_handles_empty_list(scheduler):
    assert scheduler.sort_by_time([]) == []


def test_sort_by_time_handles_unpadded_hours(scheduler):
    pet = Pet("Mochi", "cat")
    pet.add_task(Task("Dinner", 10, "low", time="18:00", due_date=DAY))
    pet.add_task(Task("Breakfast", 10, "low", time="7:30", due_date=DAY))

    result = scheduler.sort_by_time(make_owner(pet).get_all_tasks())

    assert titles(result) == ["Breakfast", "Dinner"]


# --- Recurrence ---


def test_completing_daily_task_creates_task_for_next_day(scheduler):
    pet = Pet("Leo", "dog")
    walk = Task("Walk", 30, "high", frequency="daily", time="07:00", due_date=DAY)
    pet.add_task(walk)

    next_task = scheduler.mark_task_complete(pet, walk)

    assert walk.completed is True
    assert next_task in pet.tasks
    assert len(pet.tasks) == 2
    assert next_task.due_date == date(2026, 10, 19)
    assert next_task.completed is False
    assert (next_task.title, next_task.duration_minutes, next_task.priority, next_task.time) == (
        "Walk", 30, "high", "07:00",
    )


def test_completing_weekly_task_creates_task_seven_days_later(scheduler):
    pet = Pet("Leo", "dog")
    bath = Task("Bath", 20, "medium", frequency="weekly", due_date=DAY)
    pet.add_task(bath)

    next_task = scheduler.mark_task_complete(pet, bath)

    assert next_task.due_date == date(2026, 10, 25)


def test_completing_one_time_task_creates_nothing(scheduler):
    pet = Pet("Leo", "dog")
    vet = Task("Vet visit", 60, "high", frequency="once", due_date=DAY)
    pet.add_task(vet)

    assert scheduler.mark_task_complete(pet, vet) is None
    assert vet.completed is True
    assert pet.tasks == [vet]


def test_unknown_frequency_does_not_recur():
    assert Task("Trim nails", 10, "low", frequency="monthly").next_occurrence() is None


def test_daily_recurrence_rolls_over_year_end():
    task = Task("Walk", 30, "high", frequency="daily", due_date=date(2026, 12, 31))

    assert task.next_occurrence().due_date == date(2027, 1, 1)


def test_weekly_recurrence_handles_leap_year():
    task = Task("Bath", 20, "medium", frequency="weekly", due_date=date(2028, 2, 25))

    assert task.next_occurrence().due_date == date(2028, 3, 3)


def test_completing_task_twice_does_not_duplicate_next_occurrence(scheduler):
    pet = Pet("Leo", "dog")
    walk = Task("Walk", 30, "high", frequency="daily", due_date=DAY)
    pet.add_task(walk)

    scheduler.mark_task_complete(pet, walk)
    scheduler.mark_task_complete(pet, walk)

    assert len(pet.tasks) == 2


# --- Conflict detection ---


def test_detect_conflicts_flags_two_tasks_at_same_time(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Feeding", 10, "high", time="08:00", due_date=DAY))

    warnings = scheduler.detect_conflicts(make_owner(pet))

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Feeding" in warnings[0]


def test_detect_conflicts_flags_overlap_across_different_pets(scheduler):
    dog, cat = Pet("Leo", "dog"), Pet("Mochi", "cat")
    dog.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    cat.add_task(Task("Brush", 15, "low", time="08:15", due_date=DAY))

    warnings = scheduler.detect_conflicts(make_owner(dog, cat))

    assert len(warnings) == 1
    assert "Leo and Mochi" in warnings[0]


def test_detect_conflicts_flags_task_nested_inside_another(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Hike", 60, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Snack", 5, "low", time="08:20", due_date=DAY))

    assert len(scheduler.detect_conflicts(make_owner(pet))) == 1


def test_detect_conflicts_flags_every_overlapping_pair(scheduler):
    pet = Pet("Leo", "dog")
    for title in ["A", "B", "C"]:
        pet.add_task(Task(title, 30, "low", time="09:00", due_date=DAY))

    assert len(scheduler.detect_conflicts(make_owner(pet))) == 3


def test_back_to_back_tasks_are_not_a_conflict(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Feeding", 10, "high", time="08:30", due_date=DAY))

    assert scheduler.detect_conflicts(make_owner(pet)) == []


def test_one_minute_overlap_is_a_conflict(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Feeding", 10, "high", time="08:29", due_date=DAY))

    assert len(scheduler.detect_conflicts(make_owner(pet))) == 1


def test_same_time_on_different_days_is_not_a_conflict(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=date(2026, 10, 19)))

    assert scheduler.detect_conflicts(make_owner(pet)) == []


def test_detect_conflicts_ignores_completed_and_untimed_tasks(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Done walk", 30, "high", time="08:00", due_date=DAY, completed=True))
    pet.add_task(Task("Anytime play", 30, "low", due_date=DAY))

    assert scheduler.detect_conflicts(make_owner(pet)) == []


def test_detect_conflicts_warns_on_invalid_time_and_keeps_checking(scheduler):
    pet = Pet("Leo", "dog")
    pet.add_task(Task("Broken", 10, "low", time="25:00", due_date=DAY))
    pet.add_task(Task("Walk", 30, "high", time="08:00", due_date=DAY))
    pet.add_task(Task("Feeding", 10, "high", time="08:00", due_date=DAY))

    warnings = scheduler.detect_conflicts(make_owner(pet))

    assert len(warnings) == 2
    assert any("invalid time '25:00'" in w for w in warnings)


def test_detect_conflicts_with_no_tasks_returns_empty(scheduler):
    assert scheduler.detect_conflicts(make_owner(Pet("Leo", "dog"))) == []
    assert scheduler.detect_conflicts(make_owner()) == []


# --- Filtering ---


@pytest.fixture
def household():
    dog, cat = Pet("Leo", "dog"), Pet("Mochi", "cat")
    dog.add_task(Task("Walk", 30, "high", due_date=DAY, completed=True))
    dog.add_task(Task("Feeding", 10, "high", due_date=DAY))
    cat.add_task(Task("Brush", 15, "low", due_date=DAY))
    return make_owner(dog, cat)


def test_filter_tasks_with_no_filters_returns_everything(scheduler, household):
    assert titles(scheduler.filter_tasks(household)) == ["Walk", "Feeding", "Brush"]


def test_filter_tasks_by_pet_name_ignores_case(scheduler, household):
    assert titles(scheduler.filter_tasks(household, pet_name="mochi")) == ["Brush"]


def test_filter_tasks_by_completion_status(scheduler, household):
    assert titles(scheduler.filter_tasks(household, completed=True)) == ["Walk"]
    assert titles(scheduler.filter_tasks(household, completed=False)) == ["Feeding", "Brush"]


def test_filter_tasks_combines_pet_and_status(scheduler, household):
    assert titles(scheduler.filter_tasks(household, pet_name="Leo", completed=False)) == ["Feeding"]


def test_filter_tasks_for_unknown_pet_returns_empty(scheduler, household):
    assert scheduler.filter_tasks(household, pet_name="Rex") == []


def test_filter_tasks_for_pet_with_no_tasks_returns_empty(scheduler):
    owner = make_owner(Pet("Leo", "dog"))

    assert scheduler.filter_tasks(owner, pet_name="Leo") == []
    assert owner.get_all_tasks() == []


# --- Data persistence (data.json) ---


def make_saved_household():
    rex = Pet("Rex", "dog")
    rex.add_task(Task("Walk", 30, "high", time="07:00", due_date=DAY))
    rex.add_task(Task("Bath", 45, "low", frequency="once", completed=True, due_date=DAY))
    whiskers = Pet("Whiskers", "cat")
    whiskers.add_task(Task("Brush", 10, "medium", frequency="weekly", due_date=DAY))
    owner = Owner("Sam", 90, day_start_minute=7 * 60, preferences=["mornings"])
    owner.add_pet(rex)
    owner.add_pet(whiskers)
    return owner


def test_save_and_load_round_trip_keeps_everything(tmp_path):
    path = tmp_path / "data.json"
    owner = make_saved_household()

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded == owner  # dataclass equality compares every field, nested pets and tasks included
    assert isinstance(loaded.pets[0].tasks[0].due_date, date)


def test_load_missing_file_returns_none(tmp_path):
    assert Owner.load_from_json(tmp_path / "nope.json") is None


def test_saved_file_is_readable_json_with_version(tmp_path):
    path = tmp_path / "data.json"
    make_saved_household().save_to_json(path)

    payload = json.loads(path.read_text())

    assert payload["version"] == SCHEMA_VERSION
    assert payload["owner"]["pets"][0]["tasks"][0]["due_date"] == "2026-10-18"


def test_save_leaves_no_temp_files_and_overwrites(tmp_path):
    path = tmp_path / "data.json"
    owner = make_saved_household()
    owner.save_to_json(path)

    owner.pets[0].remove_task("Walk")
    owner.save_to_json(path)

    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]
    assert titles(Owner.load_from_json(path).get_all_tasks()) == ["Bath", "Brush"]


def test_recurring_task_completed_after_reload_still_regenerates(tmp_path, scheduler):
    path = tmp_path / "data.json"
    make_saved_household().save_to_json(path)
    owner = Owner.load_from_json(path)
    whiskers = owner.pets[1]

    next_task = scheduler.mark_task_complete(whiskers, whiskers.tasks[0])

    assert next_task.due_date == date(2026, 10, 25)


@pytest.mark.parametrize(
    "contents",
    [
        "{not json",
        "[]",
        '{"version": 1}',
        '{"version": 1, "owner": {"name": "Sam"}}',
        '{"version": 1, "owner": {"name": "Sam", "available_minutes": 60, '
        '"pets": [{"name": "Rex", "tasks": [{"title": "Walk", "duration_minutes": 5, '
        '"priority": "high", "due_date": "not-a-date"}]}]}}',
    ],
)
def test_load_corrupt_file_raises_value_error(tmp_path, contents):
    path = tmp_path / "data.json"
    path.write_text(contents)

    with pytest.raises(ValueError):
        Owner.load_from_json(path)


def test_load_rejects_newer_schema_version(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"version": SCHEMA_VERSION + 1, "owner": {"name": "Sam", "available_minutes": 60}}))

    with pytest.raises(ValueError, match="version"):
        Owner.load_from_json(path)


def test_load_fills_defaults_and_ignores_unknown_keys(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({
        "owner": {
            "name": "Sam",
            "available_minutes": 60,
            "favorite_color": "blue",
            "pets": [{"name": "Rex", "tasks": [{"title": "Walk", "duration_minutes": 5, "priority": "high"}]}],
        }
    }))

    owner = Owner.load_from_json(path)
    task = owner.pets[0].tasks[0]

    assert owner.day_start_minute == 8 * 60
    assert owner.pets[0].species == "other"
    assert (task.frequency, task.completed, task.time, task.due_date) == ("daily", False, "", date.today())
