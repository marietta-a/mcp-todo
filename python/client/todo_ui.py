# todo_ui.py
# This is the UI layer of the application — built with Tkinter (Python's built-in GUI toolkit).

import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

from client.constants import Colors           # Color constants for consistent theming
from shared.todo_model import TodoModel
from client.mcp_todo_client import MCPTodoClient
from utils.todo_utils import string_to_todo  # Helper to parse JSON string → list of TodoModel
from server.config import db                   # Shared database instance


# ─────────────────────────────────────────────
# REUSABLE UI COMPONENTS
# ─────────────────────────────────────────────

class TaskItem(tk.Frame):
    """
    A self-contained UI row representing a single task.

    Each row contains:
      - A checkbox button (click to toggle complete/incomplete)
      - A task label (double-click to edit)
      - A delete button (click to remove)
      - A thin divider line at the bottom
    """

    def __init__(self, parent, task_data: TodoModel, callbacks):
        super().__init__(parent, bg=Colors.BG)
        self.task_data = task_data   # The task this row represents
        self.callbacks = callbacks   # Dictionary of functions: {on_toggle, on_edit, on_delete}
        self.pack(fill="x", padx=25, pady=2)

        is_done = task_data.completed

        # Change font style and color depending on completion status
        item_font = ("Segoe UI", 12, "overstrike") if is_done else ("Segoe UI", 12)
        fg_color = Colors.TEXT_DATE if is_done else Colors.TEXT_SUB
        check_char = "☑" if is_done else "☐"  # Visual checkbox symbol

        # ── Checkbox toggle button ──
        # Clicking this triggers the on_toggle callback with the task's ID
        self.check_btn = tk.Label(
            self, text=check_char, font=("Segoe UI", 16),
            fg=Colors.PRIMARY if is_done else "#cbd5e0",
            bg=Colors.BG, width=2, cursor="hand2"
        )
        self.check_btn.pack(side="left")
        self.check_btn.bind("<Button-1>", lambda e: self.callbacks['on_toggle'](task_data.id))

        # ── Task description label ──
        # Double-clicking this triggers the on_edit callback with the task's ID
        self.label = tk.Label(
            self, text=task_data.description,
            font=item_font, fg=fg_color, bg=Colors.BG, anchor="w", cursor="hand2"
        )
        self.label.pack(side="left", padx=5, fill="x", expand=True)
        self.label.bind("<Double-Button-1>", lambda e: self.callbacks['on_edit'](task_data.id))

        # ── Delete button ──
        # Clicking this triggers the on_delete callback with the task's ID
        self.del_btn = tk.Label(self, text="✕", font=("Segoe UI", 10), fg="#cbd5e0", bg=Colors.BG, cursor="hand2")
        self.del_btn.pack(side="right", padx=5)
        self.del_btn.bind("<Button-1>", lambda e: self.callbacks['on_delete'](task_data.id))

        # ── Divider line ──
        # A thin 1px horizontal line at the bottom of each row for visual separation
        tk.Frame(self, height=1, bg=Colors.LINE).place(relx=0, rely=0.98, relwidth=1)


class SectionHeader(tk.Frame):
    """A simple section title bar (e.g., 'Tasks' or 'Completed')."""

    def __init__(self, parent, title):
        super().__init__(parent, bg=Colors.BG)
        self.pack(fill="x", padx=25, pady=(15, 5))
        tk.Label(self, text=title, font=("Segoe UI", 12, "bold"), fg=Colors.TEXT_MAIN, bg=Colors.BG).pack(side="left")


# ─────────────────────────────────────────────
# MAIN MODULE (CONTROLLER + VIEW)
# ─────────────────────────────────────────────

class TodoModule(tk.Frame):
    """
    The main application frame.

    Responsibilities:
      - Renders the full UI (header, input, task list)
      - Connects to the MCP server via MCPTodoClient
      - Handles user interactions (add, edit, toggle, delete)
      - Keeps the displayed task list in sync with the MCP server
    """

    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BG)
        self.pack(fill="both", expand=True)

        # Local database (TodoDataManager) — used for ID generation and quick access
        self.db = db

        # MCP client — used to perform all CRUD operations through the MCP server
        self.mcp_client = MCPTodoClient()

        self.loading = False    # Guard flag to prevent overlapping load_tasks calls

        self.setup_ui()         # Build the UI widgets
        self.tasks: list[TodoModel] = []  # Local cache of tasks shown in the UI
        self.load_tasks()       # Initial task load

        # Schedule MCP connection after 100ms — gives the UI time to render first
        self.after(100, self.initialize_mcp)

    def initialize_mcp(self):
        """Kicks off the MCP connection in a background thread so the UI stays responsive."""
        self.show_status("Connecting to MCP server...")
        threading.Thread(target=self._connect_mcp, daemon=True).start()

    def show_status(self, message: str):
        """
        Briefly shows a status message in the header area.
        The message auto-clears after 3 seconds.
        """
        self.status_label.config(text=message)
        self.after(3000, lambda: self.status_label.config(text=""))

    def _connect_mcp(self):
        """
        Runs in a background thread.

        Starts the MCPTodoClient (which itself spawns another background thread
        for the asyncio loop), waits 1 second for the connection to establish,
        then triggers an initial task load.
        """
        self.mcp_client.start()

        import time
        time.sleep(1)  # Brief wait to allow the MCP server handshake to complete

        # `self.after(0, ...)` schedules load_tasks to run on the main UI thread
        # This is important — Tkinter is NOT thread-safe; UI updates must happen on the main thread
        self.after(0, self.load_tasks)

    def setup_ui(self):
        """Builds all the static UI elements: header, input bar, task list area."""

        # ── Header ──
        header = tk.Frame(self, bg=Colors.BG, padx=25, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Today", font=("Segoe UI", 18, "bold"), bg=Colors.BG).pack(anchor="w")

        # ── Task Input Row ──
        input_frame = tk.Frame(self, bg=Colors.BG, padx=25, pady=10)
        input_frame.pack(fill="x")

        # Text entry field for new task descriptions
        self.entry = tk.Entry(
            input_frame, font=("Segoe UI", 12), relief="flat",
            highlightthickness=1, highlightbackground=Colors.LINE
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

        # Pressing Enter or clicking "+ Add" both call _add_task_thread
        self.entry.bind("<Return>", lambda e: self._add_task_thread())
        tk.Button(
            input_frame, text="+ Add", command=self._add_task_thread,
            bg=Colors.PRIMARY, fg="white", relief="flat", padx=15
        ).pack(side="right")

        # ── Task List Container ──
        # This frame is cleared and rebuilt every time render_tasks() is called
        self.list_area = tk.Frame(self, bg=Colors.BG)
        self.list_area.pack(fill="both", expand=True)

        # ── Status Label ──
        # Shown in the header area; used to display connection and loading messages
        self.status_label = tk.Label(header, text="", font=("Segoe UI", 10), fg=Colors.PRIMARY, bg=Colors.BG)
        self.status_label.pack(side="right", padx=10)

    # ─────────────────────────────────────────────
    # RENDERING
    # ─────────────────────────────────────────────

    def render_tasks(self):
        """
        Clears the task list area and rebuilds it from self.tasks.

        This is a full re-render — all existing widgets are destroyed and recreated.
        Tasks are split into two sections: active ("Tasks") and completed ("Completed").
        """
        # Remove all existing task widgets
        for widget in self.list_area.winfo_children():
            widget.destroy()

        # Define callback functions passed down to each TaskItem
        callbacks = {
            'on_toggle': self._ui_toggle,
            'on_edit': self._update_tasks,
            'on_delete': self._delete_task
        }

        if len(self.tasks) > 0:
            # Section: Active tasks
            SectionHeader(self.list_area, "Tasks")
            for t in [t for t in self.tasks if not t.completed]:
                TaskItem(self.list_area, t, callbacks)

            # Section: Completed tasks
            SectionHeader(self.list_area, "Completed")
            for t in [t for t in self.tasks if t.completed]:
                TaskItem(self.list_area, t, callbacks)

    # ─────────────────────────────────────────────
    # UI EVENT HANDLERS
    # ─────────────────────────────────────────────

    def _ui_toggle(self, tid):
        """
        Toggles a task's completed status.

        1. Finds the task in the local cache
        2. Flips its completed flag
        3. Calls the MCP 'update' tool to persist the change
        4. Re-renders the task list
        """
        current_task = next((t for t in self.tasks if t.id == tid), None)
        if current_task:
            current_task.completed = not current_task.completed
            # Sync the updated task to the MCP server
            self.mcp_client.call_tool_sync("update", current_task.__dict__)
            self.render_tasks()

    # ─────────────────────────────────────────────
    # MCP DATA OPERATIONS
    # ─────────────────────────────────────────────

    def load_tasks(self):
        """
        Fetches all tasks from the MCP server and refreshes the UI.

        Uses a background thread to avoid blocking the UI while waiting for the server.
        The `loading` flag prevents multiple simultaneous requests.
        """
        if self.loading:
            return  # Already loading — skip duplicate request

        self.loading = True
        self.show_status("Loading tasks...")
        threading.Thread(target=self._load_tasks_thread, daemon=True).start()

    def _load_tasks_thread(self):
        """
        Background thread: calls the MCP 'list' tool and updates the UI.

        Calls call_tool_sync("list", {}) which internally runs the async MCP call
        on the background event loop and blocks until the result is ready.

        The JSON string result is parsed into a list of TodoModel objects,
        stored in self.tasks, and then the UI is re-rendered.
        """
        try:
            # Call the MCP 'list' tool — returns a JSON string of all tasks
            json_str = self.mcp_client.call_tool_sync("list", {})

            # Parse the JSON string into Python TodoModel objects
            result = string_to_todo(json_str)

            if isinstance(result, list):
                self.tasks = result
                # Note: render_tasks() touches Tkinter widgets, so ideally it should
                # be scheduled on the main thread with self.after(0, self.render_tasks)
                self.render_tasks()
        finally:
            self.loading = False  # Always reset the flag, even if an error occurred

    def _update_tasks(self, tid):
        """
        Opens an edit dialog for the task with the given ID,
        then calls the MCP 'update' tool to persist the change.
        """
        current_task = next((t for t in self.tasks if t.id == tid), None)
        if current_task:
            new_text = simpledialog.askstring("Edit", "Update task:", initialvalue=current_task.description)
            current_task.description = new_text
            if new_text:
                # Send updated task data to the MCP server
                self.mcp_client.call_tool_sync("update", current_task.__dict__)
                # Reload tasks to reflect the update
                self._load_tasks_thread()

    def _add_task_thread(self):
        """
        Reads the input field, creates a new task, and calls the MCP 'add' tool.

        After adding, the input field is cleared and the task list is reloaded.
        """
        todo = TodoModel(
            id=self.db._next_id,
            description=self.entry.get()
        )

        # Send the new task to the MCP server
        self.mcp_client.call_tool_sync("add", todo.__dict__)

        # Clear the input field
        self.entry.delete(0, tk.END)

        # Reload tasks from the server to confirm the add succeeded
        self._load_tasks_thread()

    def _delete_task(self, tid: int):
        """
        Asks for confirmation, then calls the MCP 'delete' tool with the task's ID.
        Reloads the task list after deletion.
        """
        if messagebox.askyesno("Delete", "Delete this task?"):
            record = {"id": tid}
            # Call the MCP 'delete' tool — only the ID is needed
            self.mcp_client.call_tool_sync("delete", record)
            # Reload tasks to confirm the delete
            self._load_tasks_thread()

    def destroy(self):
        """
        Called when the window is closed.
        Stops the MCP client cleanly before destroying the Tkinter frame.
        """
        self.mcp_client.stop()
        super().destroy()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Clean CRUD Architecture")
    root.geometry("500x500")

    def on_closing():
        """Ensures the MCP client is stopped before the window closes."""
        if hasattr(app, 'destroy'):
            app.destroy()
        root.destroy()

    app = TodoModule(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Hook window close button
    root.mainloop()  # Start the Tkinter event loop