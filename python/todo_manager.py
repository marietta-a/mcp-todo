# --- CRUD LOGIC CLASS (THE MODEL) ---
class TodoDataManager:
    """Handles all CRUD operations independently of the UI."""
    def __init__(self):
        self._tasks = []
        self._next_id = 1
        # Seed initial data
        self.add_task("Buy groceries")
        self.add_task("Call mom")
        self.add_task("Walk the dog", completed=True)

    def add_task(self, text, completed=False):
        """CREATE: Adds a new task."""
        if text.strip():
            task = {"id": self._next_id, "text": text.strip(), "completed": completed}
            self._tasks.append(task)
            self._next_id += 1
            return task
        return None

    def get_all_tasks(self):
        """READ: Returns all tasks."""
        return self._tasks

    def update_task_text(self, task_id, new_text):
        """UPDATE: Changes the text of a task."""
        for task in self._tasks:
            if task['id'] == task_id:
                task['text'] = new_text
                return True
        return False

    def toggle_task_status(self, task_id):
        """UPDATE: Toggles completed status."""
        for task in self._tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                return True
        return False

    def delete_task(self, task_id):
        """DELETE: Removes a task."""
        self._tasks = [t for t in self._tasks if t['id'] != task_id]