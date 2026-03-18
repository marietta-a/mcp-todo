from todo_model import TodoModel

# --- CRUD LOGIC CLASS (THE MODEL) ---
class TodoDataManager:
    """Handles all CRUD operations independently of the UI."""
    def __init__(self):
        self._tasks: list[TodoModel] = []
        self._next_id = 0
        # Seed initial data
        self.add_task(TodoModel(id=self._next_id, description="Buy groceries", completed=False))
        self.add_task(TodoModel(id=self._next_id, description="Call mom", completed=False))
        self.add_task(TodoModel(id=self._next_id, description="Walk the dog", completed=True))

    def add_task(self, todo: TodoModel):
        """CREATE: Adds a new task."""
        if todo.description.strip():
            todo.id = self._next_id
            self._tasks.append(todo)
            self._next_id += 1
            return todo
        return None

    def get_all_tasks(self):
        """READ: Returns all tasks."""
        return self._tasks

    def update_task(self, todo: TodoModel):
        """UPDATE: Changes the text of a task."""
        for task in self._tasks:
            if task.id == todo.id:
                task.description = todo.description
                task.completed = todo.completed
                return True
        return False

    def toggle_task_status(self, task_id):
        """UPDATE: Toggles completed status."""
        for task in self._tasks:
            if task.id == task_id:
                task.completed = not task.completed
                return True
        return False

    def delete_task(self, task_id):
        """DELETE: Removes a task."""
        self._tasks = [t for t in self._tasks if t.id != task_id]