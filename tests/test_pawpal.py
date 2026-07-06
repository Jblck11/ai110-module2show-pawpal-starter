"""Quick tests for the PawPal+ logic layer."""

from pawpal_system import CareTask, Pet


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task's completed status to True."""
    task = CareTask("Morning walk", duration_minutes=20, priority="high")

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet("Mochi", "cat")

    assert len(pet.tasks) == 0  # starts with no tasks

    pet.add_task(CareTask("Feeding", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == 1
