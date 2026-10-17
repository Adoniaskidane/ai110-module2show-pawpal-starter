import streamlit as st

from pawpal_system import Owner, Pet, Task

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

# Streamlit reruns this whole script on every interaction, so the Owner lives in
# st.session_state (a per-session dict) and is only created on the first run.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner: Owner = st.session_state.owner

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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == pet_choice)
            pet.add_task(
                Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{task_title}' for {pet.name}.")
else:
    st.caption("Add a pet first, then you can give it tasks.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": pet.name,
                "title": task.title,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "frequency": task.frequency,
                "done": task.completed,
            }
            for pet, task in all_tasks
        ]
    )
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    st.warning(
        "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
    )
    st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )
