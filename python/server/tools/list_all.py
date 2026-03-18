from todo_model import TodoModel
from config import db
from .schema import EmptySchama


async def task_list_handler(args) -> list[TodoModel]:
    try:
        input_model = EmptySchama(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")
    
    """Handle task listings"""
    return db.get_all_tasks(input_model)

list_all = {
    "name": "list",
    "description": "List all tasks",
    "input_schema": EmptySchama,
    "handler": task_list_handler
}