# add.py
# This file defines the "add" MCP tool.
#
# In MCP (Model Context Protocol), a "tool" is a function that an AI or client
# can call by name to perform an action. Each tool has:
#   - a name       : how the tool is identified when called
#   - a description: what the tool does (shown to the AI/client)
#   - an input_schema: the shape of data the tool expects (validated by Pydantic)
#   - a handler    : the async function that actually runs when the tool is called

from shared.todo_model import TodoModel  # The data model for a single to-do task
from server.config import db             # Our shared in-memory database instance


async def add_handler(args) -> TodoModel:
    """
    This is the handler function — it runs when the 'add' tool is called.

    `args` is a dictionary of input values sent by the caller.
    We first validate it against TodoModel to ensure the data is correct,
    then we add the new task to our database.
    """
    try:
        # Validate and convert the raw dictionary into a TodoModel object.
        # If required fields are missing or the wrong type, Pydantic raises an error.
        input_model = TodoModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    # Add the validated task to the database and return the saved task
    return db.add_task(input_model)


# This dictionary is the actual "tool definition" that gets registered with the MCP server.
# The server reads `name`, `description`, and `input_schema` to advertise the tool to clients.
# When the tool is called, the server runs `handler` with the provided arguments.
add = {
    "name": "add",                          # The tool's unique name (clients call it by this name)
    "description": "Creates a new task",    # Human-readable explanation of what the tool does
    "input_schema": TodoModel,              # Pydantic model used to validate input & generate schema
    "handler": add_handler                  # The async function to execute when the tool is called
}