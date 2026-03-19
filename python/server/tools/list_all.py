# list_all.py
# This file defines the "list" MCP tool.
#
# The list tool retrieves all tasks currently stored in the database.
# It takes no input (hence EmptySchema), and returns a list of TodoModel objects.

from shared.todo_model import TodoModel    # The data model for a single task
from server.config import db               # Our shared in-memory database instance
from .schema import EmptySchama     # A schema with no fields — this tool needs no input


async def task_list_handler(args) -> list[TodoModel]:
    """
    Handler for the 'list' tool.

    `args` will be an empty dictionary {} since this tool takes no input.
    We still validate it with EmptySchema to keep the code consistent
    with all other tool handlers.

    Returns a list of all tasks in the database.
    """
    try:
        # Validate the (empty) input — this is mostly a formality here
        input_model = EmptySchama(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    # Fetch and return all tasks from the database
    return db.get_all_tasks()


# Tool definition dictionary registered with the MCP server.
# Takes no input and returns all stored tasks.
list_all = {
    "name": "list",                 # The tool's unique name (note: "list" is the callable name)
    "description": "List all tasks",# What this tool does
    "input_schema": EmptySchama,    # No input fields required
    "handler": task_list_handler    # Function to call when the tool is invoked
}