# todo_model.py
# This file defines the core data model for a single to-do task.
#
# In MCP (and most Python backends), we use Pydantic's BaseModel to define
# data models. Pydantic gives us three things for free:
#   1. VALIDATION  — it checks that fields have the correct types when a model is created
#   2. SERIALIZATION — it can convert the model to/from JSON automatically
#   3. SCHEMA GENERATION — it can describe the model's shape as a JSON Schema
#                          (which the MCP server uses to advertise tool input requirements)

from pydantic import BaseModel


class TodoModel(BaseModel):
    """
    Represents a single to-do task.

    This model is shared across the entire project:
      - The MCP tools (add, update) use it to validate incoming data
      - The database (TodoDataManager) stores instances of this model
      - The UI (TodoModule) reads instances of this model to render task rows
      - The MCP server uses its schema to describe what the 'add' and 'update' tools expect

    Fields:
      id          : A unique integer that identifies this task.
                    Assigned automatically by TodoDataManager when the task is created.
      completed   : Whether the task is done. Defaults to False (not completed).
      description : The text content of the task (e.g. "Buy groceries").
    """

    id: int               # Unique identifier for the task (set by the database)
    completed: bool = False  # Task status — False = pending, True = done (default: False)
    description: str      # The human-readable text describing the task

    def clone(self) -> 'TodoModel':
        """
        Creates and returns an independent copy of this task.

        This is useful when you want to modify a task without affecting the original.
        For example, when toggling completion status in the UI, you might clone the
        task first so the original stays unchanged until the update is confirmed.

        Note: Pydantic v2 also provides model.model_copy() for this purpose,
        but this custom method makes the intent explicit for beginners.

        Returns:
            A new TodoModel instance with the same id, description, and completed values.
        """
        return TodoModel(
            id=self.id,
            description=self.description,
            completed=self.completed
        )