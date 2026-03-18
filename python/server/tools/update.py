from config import db
from todo_model import TodoModel

async def update_handler(args) -> bool:
    try:
        input_model = TodoModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")
    
    """Handle task update"""
    return db.update_task(input_model)

update = {
    "name": "update",
    "description": "Update an existing task",
    "input_schema": TodoModel,
    "handler": update_handler
}
