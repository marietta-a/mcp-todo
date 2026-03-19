import json
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
from typing import Union

from constants import Colors
from todo_manager import TodoDataManager
from todo_model import TodoModel
from mcp_todo_client import MCPTodoClient
from utils.todo_utils import string_to_todo
from config import db

class TaskItem(tk.Frame):
    """Component for a single task row."""
    def __init__(self, parent, task_data: TodoModel, callbacks):
        super().__init__(parent, bg=Colors.BG)
        self.task_data = task_data
        # Dictionary of function references
        self.callbacks = callbacks 
        self.pack(fill="x", padx=25, pady=2)

        is_done = task_data.completed
        item_font = ("Segoe UI", 12, "overstrike") if is_done else ("Segoe UI", 12)
        fg_color = Colors.TEXT_DATE if is_done else Colors.TEXT_SUB
        check_char = "☑" if is_done else "☐"

        # Checkbox Toggle
        self.check_btn = tk.Label(self, text=check_char, font=("Segoe UI", 16),
            fg=Colors.PRIMARY if is_done else "#cbd5e0", bg=Colors.BG, width=2, cursor="hand2")
        self.check_btn.pack(side="left")
        self.check_btn.bind("<Button-1>", lambda e: self.callbacks['on_toggle'](task_data.id))

        # Task Text Label (Double click to edit)
        self.label = tk.Label(self, text=task_data.description, font=item_font,
            fg=fg_color, bg=Colors.BG, anchor="w", cursor="hand2")
        self.label.pack(side="left", padx=5, fill="x", expand=True)
        self.label.bind("<Double-Button-1>", lambda e: self.callbacks['on_edit'](task_data.id))

        # Delete Button
        self.del_btn = tk.Label(self, text="✕", font=("Segoe UI", 10), fg="#cbd5e0", bg=Colors.BG, cursor="hand2")
        self.del_btn.pack(side="right", padx=5)
        self.del_btn.bind("<Button-1>", lambda e: self.callbacks['on_delete'](task_data.id))

        # Divider line
        tk.Frame(self, height=1, bg=Colors.LINE).place(relx=0, rely=0.98, relwidth=1)

class SectionHeader(tk.Frame):
    """Component for section titles."""
    def __init__(self, parent, title):
        super().__init__(parent, bg=Colors.BG)
        self.pack(fill="x", padx=25, pady=(15, 5))
        tk.Label(self, text=title, font=("Segoe UI", 12, "bold"), fg=Colors.TEXT_MAIN, bg=Colors.BG).pack(side="left")

# --- MAIN MODULE (THE CONTROLLER INTERFACE) ---

class TodoModule(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BG)
        self.pack(fill="both", expand=True)
        
        # Instantiate the CRUD Manager
        self.db = db
        # Instantiat MCPTodo client
        self.mcp_client = MCPTodoClient()

        self.loading = False

        self.setup_ui()
        self.tasks: list[TodoModel] = []
        self.load_tasks()

        
        # Start MCP client and load initial data
        self.after(100, self.initialize_mcp)


    def initialize_mcp(self):
        """Initialize MCP connection in background"""
        self.show_status("Connecting to MCP server...")
        
        # Start MCP client in a thread
        threading.Thread(target=self._connect_mcp, daemon=True).start()
        
    def show_status(self, message: str):
        """Show status message in UI"""
        self.status_label.config(text=message)
        self.after(3000, lambda: self.status_label.config(text=""))

    def _connect_mcp(self):
        """Connect to MCP and load tasks (runs in background thread)"""
        self.mcp_client.start()
        
        # Give it a moment to connect
        import time
        time.sleep(1)
        
        # Load initial tasks
        self.after(0, self.load_tasks)      



    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg=Colors.BG, padx=25, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Today", font=("Segoe UI", 18, "bold"), bg=Colors.BG).pack(anchor="w")

        # Create Task Input
        input_frame = tk.Frame(self, bg=Colors.BG, padx=25, pady=10)
        input_frame.pack(fill="x")
        self.entry = tk.Entry(input_frame, font=("Segoe UI", 12), relief="flat", highlightthickness=1, highlightbackground=Colors.LINE)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._add_task_thread())

        tk.Button(input_frame, text="+ Add", command=self._add_task_thread, bg=Colors.PRIMARY, fg="white", relief="flat", padx=15).pack(side="right")

        # Task Containers
        self.list_area = tk.Frame(self, bg=Colors.BG)
        self.list_area.pack(fill="both", expand=True)

        
        # Status label
        self.status_label = tk.Label(header, text="", font=("Segoe UI", 10),
                                     fg=Colors.PRIMARY, bg=Colors.BG)
        self.status_label.pack(side="right", padx=10)

    # --- UI EVENT HANDLERS (Calling the DataManager) ---

    def render_tasks(self):
        """Clears and re-renders the list based on current data."""
        for widget in self.list_area.winfo_children():
            widget.destroy()

        # tasks = self.db.get_all_tasks()
        callbacks = {
            'on_toggle': self.ui_toggle,
            'on_edit': self._update_tasks,
            'on_delete': self._delete_task
        }

        if self.tasks.__len__() > 0:
          # Render Active
          SectionHeader(self.list_area, "Tasks")
          for t in [t for t in self.tasks if not t.completed]:
            TaskItem(self.list_area, t, callbacks)

          # Render Completed
          SectionHeader(self.list_area, "Completed")
          for t in [t for t in self.tasks if t.completed]:
            TaskItem(self.list_area, t, callbacks)

    def ui_add(self):
        todo = TodoModel(
            id=self.db._next_id,
            description=self.entry.get()
        )
        self.db.add_task(todo)
        self.entry.delete(0, tk.END)
        self.render_tasks()

    def ui_toggle(self, tid):
        current_task = next((t for t in self.tasks if t.id == tid), None)
        if current_task:
          current_task.completed = not current_task.completed
          task_str = current_task.model_dump_json()
          self.mcp_client.call_tool_sync("update", task_str)
          self.render_tasks()

    def ui_delete(self, tid):
        if messagebox.askyesno("Delete", "Delete this task?"):
            self.db.delete_task(tid)
            self.render_tasks()

    def ui_edit(self, tid):
        # Find current text for the dialog
        current_task = next(t for t in self.db.get_all_tasks() if t.id == tid)
        new_text = simpledialog.askstring("Edit", "Update task:", initialvalue=current_task.description)
        current_task.description = new_text
        if new_text:
            self.db.update_task(current_task)
            self.render_tasks()

    def _edit_task_thread(self, task_id: int, new_description: str):
        """Background thread for editing task"""
        # Get current completed status (you'd need to store this)
        result = self.mcp_client.call_tool_sync("update", {
            "id": task_id,
            "description": new_description,
            "completed": False  # You need actual data
        })
        
        self.after(0, self.load_tasks)
        
    def load_tasks(self):
        """Load tasks from MCP server"""
        if self.loading:
            return
        
        self.loading = True
        self.show_status("Loading tasks...")
        
        # Run in background thread
        threading.Thread(target=self._load_tasks_thread, daemon=True).start()        

    def _load_tasks_thread(self):
        """Background thread for loading tasks"""
        try:
            # Get tools list (optional)
            # tools = self.mcp_client.list_tools_sync()
            # print(tools)
            # Get tasks
            json_str = self.mcp_client.call_tool_sync("list", {})
            result = string_to_todo(json_str)
            if isinstance(result, list):
              self.tasks = result
            #   self.after(0, self._update_tasks, result)
              self.render_tasks()
        finally:
            self.loading = False


    def _update_tasks(self, tid):
        # Find current text for the dialog
        current_task = next((t for t in self.tasks if t.id == tid), None)
        if current_task:
          new_text = simpledialog.askstring("Edit", "Update task:", initialvalue=current_task.description)
          current_task.description = new_text
          if new_text:
            self.mcp_client.call_tool_sync("update", current_task.__dict__)
            self._load_tasks_thread()


    def _add_task_thread(self):
        todo = TodoModel(
            id=self.db._next_id,
            description=self.entry.get()
        )
        
        self.mcp_client.call_tool_sync("add", todo.__dict__)
        self.entry.delete(0, tk.END)
        self._load_tasks_thread()
    

    def _delete_task(self, tid: int):
        if messagebox.askyesno("Delete", "Delete this task?"):
            record = {
                "id": tid
            }
            self.mcp_client.call_tool_sync("delete", record)
            self._load_tasks_thread()

    def destroy(self):
        """Clean up MCP client when closing"""
        self.mcp_client.stop()
        super().destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Clean CRUD Architecture")
    root.geometry("400x700")
    # Handle window close
    def on_closing():
        if hasattr(app, 'destroy'):
            app.destroy()
        root.destroy()
    
    app = TodoModule(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()