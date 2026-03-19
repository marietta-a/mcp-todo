# update.py
# This file defines the "update" MCP tool.
#
# The update tool modifies an existing task's description and/or completion status.
# It expects a full TodoModel as input (id + description + completed),
# finds the matching task in the database, and overwrites its fields.

from config import db           # Our shared in-memory database instance
from todo_model import TodoModel # The full task data model


async def update_handler(args) -> bool:
    """
    Handler for the 'update' tool.

    `args` should look like: {"id": 1, "description": "New text", "completed": false}
    We validate it against TodoModel, then pass it to the database for updating.

    Returns True if the task was found and updated, False otherwise.
    """
    try:
        # Validate that all required fields are present and correctly typed
        input_model = TodoModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    # Update the task in the database and return the result (True/False)
    return db.update_task(input_model)


# Tool definition dictionary registered with the MCP server.
# Requires the full task details (id, description, completed) to perform the update.
update = {
    "name": "update",                           # The tool's unique name
    "description": "Update an existing task",   # What this tool does
    "input_schema": TodoModel,                  # Full task model required as input
    "handler": update_handler                   # Function to call when the tool is invoked
}