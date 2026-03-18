from config import db
from .schema import IDSchema

async def delete_handler(args):
    try:
        input_model = IDSchema(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")
    
    """Handle task delete"""
    return db.delete_task(input_model)

delete = {
    "name": "delete",
    "description": "Delete an existing task",
    "input_schema": IDSchema,
    "handler": delete_handler
}