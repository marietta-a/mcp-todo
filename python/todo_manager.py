# todo_manager.py
# This file contains the TodoDataManager class — the "database layer" of our app.
#
# Since this is a learning project, we don't use a real database (like SQLite or PostgreSQL).
# Instead, we store tasks in a plain Python list in memory.
# This keeps things simple and easy to understand.

from todo_model import TodoModel  # Import our task data model


class TodoDataManager:
    """
    Handles all CRUD operations on tasks.
    CRUD stands for: Create, Read, Update, Delete — the four basic data operations.
    """

    def __init__(self):
        # This list holds all tasks in memory (resets when the app restarts)
        self._tasks: list[TodoModel] = []

        # Auto-incrementing counter used to assign unique IDs to each task.
        # Every time a task is added, this number increases by 1.
        self._next_id = 0

        # Seed the database with some sample tasks so the app isn't empty on launch
        self.add_task(TodoModel(id=self._next_id, description="Buy groceries", completed=False))
        self.add_task(TodoModel(id=self._next_id, description="Call mom", completed=False))
        self.add_task(TodoModel(id=self._next_id, description="Schedule appointment", completed=True))

    def add_task(self, todo: TodoModel):
        """
        CREATE: Adds a new task to the list.

        We check that the description isn't empty or just whitespace before saving.
        The task's ID is set here using the auto-incrementing `_next_id` counter.
        Returns the saved task, or None if the description was blank.
        """
        if todo.description.strip():  # Only add if description has real content
            todo.id = self._next_id   # Assign the next available ID
            self._tasks.append(todo)  # Add the task to our in-memory list
            self._next_id += 1        # Increment the counter for the next task
            return todo
        return None  # Return None if the description was empty

    def get_all_tasks(self):
        """
        READ: Returns the full list of tasks.

        This is used by the "list" MCP tool to retrieve all stored tasks.
        """
        return self._tasks

    def update_task(self, todo: TodoModel):
        """
        UPDATE: Finds an existing task by ID and updates its fields.

        We loop through the task list looking for a matching ID.
        If found, we overwrite the description and completed status.
        Returns True if found and updated, False if no match was found.
        """
        for task in self._tasks:
            if task.id == todo.id:
                task.description = todo.description
                task.completed = todo.completed
                return True  # Update succeeded
        return False  # No task with that ID exists

    def delete_task(self, task_id: int):
        """
        DELETE: Removes the task with the given ID from the list.

        We use a list comprehension to rebuild `_tasks` without the deleted item.
        This is a common Python pattern for filtering out one element from a list.
        """
        # Keep all tasks EXCEPT the one whose ID matches task_id
        self._tasks = [t for t in self._tasks if t.id != task_id]