import streamlit as st

from pawpal_system import CareTask, Pet, Owner, Scheduler

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

# --- Application "memory" -------------------------------------------------
# Streamlit reruns this whole file top-to-bottom on every interaction, so any
# object created plainly at module level is rebuilt (and emptied) each time.
# st.session_state is the per-session "vault" that survives reruns. We guard
# with `not in` so the Owner is created ONCE and then reused on every rerun.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=60)

owner = st.session_state.owner

# --- Owner --------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Time available today (minutes)",
        min_value=0, max_value=1440, value=owner.available_minutes,
    )
)

st.divider()

# --- Add a pet ----------------------------------------------------------
# A submitted pet form is handled by Owner.add_pet(): it appends the new Pet
# to the persisted Owner in session_state. Because we mutate that stored
# object, the change survives the rerun and the pet list below reflects it.
st.subheader("Pets")
pcol1, pcol2 = st.columns(2)
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip():
        owner.add_pet(Pet(pet_name.strip(), species))
        st.success(f"Added {pet_name} to {owner.name}'s pets.")
    else:
        st.warning("Give the pet a name first.")

if not owner.pets:
    st.info("No pets yet. Add one above.")

# --- Add a task to a pet ------------------------------------------------
st.markdown("### Tasks")
if owner.pets:
    target_name = st.selectbox("Add task to which pet?", [p.name for p in owner.pets])

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        # Find the chosen Pet and let Pet.add_task() handle the new CareTask.
        pet = next(p for p in owner.pets if p.name == target_name)
        pet.add_task(CareTask(task_title, int(duration), priority))
        st.success(f"Added '{task_title}' to {pet.name}.")

    # Show current tasks per pet, read straight from the persisted objects.
    for pet in owner.pets:
        st.write(f"**{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")
        if pet.tasks:
            st.table(
                [
                    {
                        "title": t.title,
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority,
                        "done": t.completed,
                    }
                    for t in pet.tasks
                ]
            )
else:
    st.caption("Add a pet before adding tasks.")

st.divider()

# --- Build schedule -----------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = Scheduler(owner).build_plan()
    if plan.scheduled:
        st.write(f"### Today's plan for {owner.name}")
        st.table(plan.to_table())
        st.markdown("**Why this plan:**")
        st.text(plan.explain())
        st.caption(
            f"Total scheduled: {plan.total_time()} min · "
            f"{len(plan.skipped)} task(s) skipped."
        )
    else:
        st.info("Nothing to schedule. Add tasks (and set available time) first.")
