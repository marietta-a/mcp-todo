# schema.py
# This file defines simple "schemas" — blueprints that describe the shape of data
# that our MCP tools expect as input.
#
# We use Pydantic's BaseModel to define these schemas.
# Pydantic automatically validates that the right data types are passed in,
# and it generates a JSON schema that MCP uses to describe each tool's inputs.

from pydantic import BaseModel

# EmptySchema is used for tools that don't need any input (like "list all tasks").
# It has no fields, but we still pass it through Pydantic so the system stays consistent.
class EmptySchama(BaseModel):
    pass  # No fields needed — this tool takes no arguments

# IDSchema is used for tools that only need a task ID (like "delete a task").
class IDSchema(BaseModel):
    id: int  # The unique identifier of the task to act on