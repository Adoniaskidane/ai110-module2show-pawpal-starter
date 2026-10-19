import json
import os
from datetime import date, datetime

import streamlit as st

from pawpal_system import DATA_FILE, SCHEMA_VERSION, Owner, Pet, Scheduler, Task

PRIORITY_LABELS = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()


def default_owner() -> Owner:
    return Owner(name="Jordan", available_minutes=120)


# Streamlit reruns this whole script on every interaction, so the Owner lives in
# st.session_state (a per-session dict). On the first run it's loaded from data.json,
# so pets and tasks survive closing the app.
if "owner" not in st.session_state:
    try:
        loaded = Owner.load_from_json(DATA_FILE)
    except ValueError as err:
        # Don't crash or silently overwrite a damaged file: set it aside and start fresh.
        backup = f"{DATA_FILE}.corrupt-{datetime.now():%Y%m%d-%H%M%S}"
        os.replace(DATA_FILE, backup)
        st.session_state.load_warning = (
            f"Couldn't read {DATA_FILE} ({err}). It was moved to {backup} and PawPal+ started fresh."
        )
        loaded = None
    st.session_state.owner = loaded or default_owner()
    # Snapshot of what's on disk; autosave() only writes when the owner differs from it.
    st.session_state.saved_snapshot = st.session_state.owner.to_dict() if loaded else None
    st.session_state.saved_at = None

owner: Owner = st.session_state.owner


def autosave() -> None:
    """Write data.json if anything changed since the last save."""
    snapshot = owner.to_dict()
    if snapshot == st.session_state.saved_snapshot:
        return
    if st.session_state.saved_snapshot is None and snapshot == default_owner().to_dict():
        return  # untouched first run: nothing worth saving yet
    try:
        owner.save_to_json(DATA_FILE)
    except OSError as err:
        st.error(f"Couldn't save to {DATA_FILE}: {err}")
        return
    st.session_state.saved_snapshot = snapshot
    st.session_state.saved_at = datetime.now()


if "load_warning" in st.session_state:
    st.warning(st.session_state.pop("load_warning"))

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Available minutes today", min_value=0, max_value=1440, value=owner.available_minutes
    )
)

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name can't be empty.")
        elif any(p.name == pet_name for p in owner.pets):
            st.error(f"{owner.name} already has a pet named {pet_name}.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species))
            st.success(f"Added {pet_name}.")

if owner.pets:
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

if owner.pets:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            task_time = st.text_input("Start time (HH:MM)", placeholder="07:30, or leave blank")
        col4, col5 = st.columns(2)
        with col4:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col5:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
                time=task_time.strip(),
            )
            try:
                if new_task.time:
                    new_task.minutes_after_midnight()  # reject "7pm", "25:00", etc.
            except ValueError:
                st.error(f"'{task_time}' isn't a valid time. Use 24-hour HH:MM, like 07:30 or 18:00.")
            else:
                pet = next(p for p in owner.pets if p.name == pet_choice)
                pet.add_task(new_task)
                st.success(f"Added '{task_title}' for {pet.name}.")
else:
    st.caption("Add a pet first, then you can give it tasks.")

scheduler = Scheduler()


def task_rows(pairs):
    """Turn (pet, task) pairs into table rows for st.table."""
    return [
        {
            "date": task.due_date.strftime("%a %b %d"),
            "time": task.time or "anytime",
            "pet": pet.name,
            "task": task.title,
            "minutes": task.duration_minutes,
            "priority": PRIORITY_LABELS.get(task.priority, task.priority),
            "repeats": task.frequency,
            "status": "✅ done" if task.completed else "⏳ to do",
        }
        for pet, task in pairs
    ]


if owner.get_all_tasks():
    st.markdown("#### Find tasks")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.radio("Status", ["To do", "Done", "All"], horizontal=True)

    filtered = scheduler.filter_tasks(
        owner,
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"To do": False, "Done": True, "All": None}[status_filter],
    )
    if filtered:
        st.caption(f"{len(filtered)} task(s), sorted by date and time. Tasks with no set time are listed last each day.")
        st.table(task_rows(scheduler.sort_by_time(filtered)))
    else:
        st.info("No tasks match these filters.")

    st.markdown("#### Update a task")
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    open_tasks = scheduler.sort_by_time(scheduler.filter_tasks(owner, completed=False))
    if open_tasks:
        with st.form("update_task"):
            choice = st.selectbox(
                "Task",
                range(len(open_tasks)),
                format_func=lambda i: (
                    f"{open_tasks[i][1].due_date:%b %d} {open_tasks[i][1].time or 'anytime'} - "
                    f"{open_tasks[i][0].name}: {open_tasks[i][1].title}"
                ),
            )
            new_time = st.text_input("New start time (HH:MM)", placeholder="leave blank for anytime")
            col1, col2, col3 = st.columns(3)
            done_clicked = col1.form_submit_button("Mark done")
            time_clicked = col2.form_submit_button("Change time")
            remove_clicked = col3.form_submit_button("Remove task")

            pet, task = open_tasks[choice]
            message = None
            if done_clicked:
                next_task = scheduler.mark_task_complete(pet, task)
                message = f"Nice! '{task.title}' is done for {pet.name}."
                if next_task:
                    message += f" The next one is scheduled for {next_task.due_date:%A, %b %d}."
            elif time_clicked:
                old_time = task.time
                task.time = new_time.strip()
                try:
                    if task.time:
                        task.minutes_after_midnight()  # reject "7pm", "25:00", etc.
                except ValueError:
                    task.time = old_time
                    st.error(f"'{new_time}' isn't a valid time. Use 24-hour HH:MM, like 07:30 or 18:00.")
                else:
                    message = f"Moved {pet.name}'s '{task.title}' to {task.time or 'anytime'}."
            elif remove_clicked:
                # Remove this exact task. Pet.remove_task(title) would also delete other
                # tasks with the same title, like tomorrow's copy of a daily task.
                pet.tasks.remove(task)
                message = f"Removed {pet.name}'s '{task.title}'."
            if message:
                # Rerun so the tables above refresh; keep the message so it survives the rerun.
                st.session_state.flash = message
                autosave()  # st.rerun() stops this run before the save at the bottom
                st.rerun()
    else:
        st.success("Everything is done. 🎉")
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Today's Schedule")

conflicts = scheduler.detect_conflicts(owner)
if conflicts:
    st.warning(
        f"**{len(conflicts)} scheduling conflict(s) found.** You can't be in two places at once, "
        "so these tasks need attention:"
    )
    for message in conflicts:
        st.markdown(f"- {message.removeprefix('WARNING: ')}")
    st.caption(
        "💡 To fix a conflict, use **Update a task** above to give one of the tasks a "
        "different start time, or mark it done if it's already taken care of."
    )
elif owner.get_all_tasks():
    st.success("No time conflicts. Every timed task has its own slot.")

today = date.today()
todays_tasks = [
    (pet, task)
    for pet, task in scheduler.filter_tasks(owner, completed=False)
    if task.due_date == today
]
if todays_tasks:
    total = sum(task.duration_minutes for _, task in todays_tasks)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks today", len(todays_tasks))
    col2.metric("Minutes needed", total)
    col3.metric("Minutes available", owner.available_minutes)
    if total > owner.available_minutes:
        st.warning(
            f"Today's tasks need {total} minutes, but only {owner.available_minutes} are available. "
            "Consider moving a low-priority task to another day."
        )
    st.table(task_rows(scheduler.sort_by_time(todays_tasks)))
else:
    st.info("Nothing left to do today.")

# Save once per run, after every widget and form above has had a chance to change the owner.
autosave()

with st.sidebar:
    st.header("💾 Saved data")
    if st.session_state.saved_at:
        st.caption(f"Auto-saved to `{DATA_FILE}` at {st.session_state.saved_at:%H:%M:%S}.")
    elif st.session_state.saved_snapshot is not None:
        st.caption(f"Loaded from `{DATA_FILE}`. Changes save automatically.")
    else:
        st.caption(f"Nothing saved yet. Your pets and tasks save to `{DATA_FILE}` automatically.")

    pet_count, task_count = len(owner.pets), len(owner.get_all_tasks())
    st.markdown(f"**{pet_count}** pet(s), **{task_count}** task(s)")

    st.download_button(
        "Download backup",
        data=json.dumps({"version": SCHEMA_VERSION, "owner": owner.to_dict()}, indent=2),
        file_name=f"pawpal-backup-{date.today()}.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("Start over"):
        st.caption(f"Deletes every pet and task and removes `{DATA_FILE}`. Rename a backup to `{DATA_FILE}` to restore it.")
        confirm = st.checkbox("Yes, erase my PawPal+ data", key="confirm_erase")
        if st.button("Erase all data", type="primary", disabled=not confirm, use_container_width=True):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            for key in ("owner", "saved_snapshot", "saved_at", "flash", "confirm_erase"):
                st.session_state.pop(key, None)
            st.rerun()
