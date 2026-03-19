# todo_utils.py
import json
from typing import List, Union
from shared.todo_model import TodoModel

def string_to_todo(text: str) -> Union[TodoModel, List[TodoModel], None]:
    """
    Convert string to TodoModel or list of TodoModels
    Returns None if parsing fails
    """
    if not text or text.startswith("Error"):
        return None
    
    try:
        data = json.loads(text)
        
        # Handle list of todos
        if isinstance(data, list):
            todos = []
            for item in data:
                try:
                    todos.append(TodoModel(**item))
                except (TypeError, ValueError) as e:
                    print(f"Skipping invalid todo item: {e}")
            return todos
        
        # Handle single todo
        elif isinstance(data, dict):
            return TodoModel(**data)
        
        else:
            return None
            
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None