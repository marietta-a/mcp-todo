from todo_model import TodoModel
from config import db

async def add_handler(args) -> TodoModel:
    try:
        input_model = TodoModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")
    
    """Handler function to add a new Task"""
    return db.add_task(input_model)

add = {
    "name": "add",
    "description": "Creates a new task",
    "input_schema": TodoModel,
    "handler": add_handler
}