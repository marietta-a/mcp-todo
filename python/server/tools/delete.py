# delete.py
# This file defines the "delete" MCP tool.
#
# The delete tool removes a task from the database using its unique ID.
# It only needs the task's `id` as input, so we use the lightweight IDSchema
# instead of the full TodoModel.

from server.config import db           # Our shared in-memory database instance
from .schema import IDSchema    # A minimal schema that only contains an `id` field


async def delete_handler(args):
    """
    Handler for the 'delete' tool.

    `args` is expected to be a dictionary like: {"id": 3}
    We validate it with IDSchema, then ask the database to remove that task.
    """
    try:
        # Validate the input — ensures `id` is present and is an integer
        input_model = IDSchema(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    # Delete the task with the given ID from the database
    return db.delete_task(input_model.id)


# Tool definition dictionary registered with the MCP server.
# Only requires an `id` — no need to pass the full task details for deletion.
delete = {
    "name": "delete",                           # The tool's unique name
    "description": "Delete an existing task",   # What this tool does
    "input_schema": IDSchema,                   # Only needs an `id` field as input
    "handler": delete_handler                   # Function to call when the tool is invoked
}