import tkinter as tk
from tkinter import simpledialog, messagebox

from python.constants import Colors
from todo_manager import TodoDataManager

class TaskItem(tk.Frame):
    """Component for a single task row."""
    def __init__(self, parent, task_data, callbacks):
        super().__init__(parent, bg=Colors.BG)
        self.task_data = task_data
        # Dictionary of function references
        self.callbacks = callbacks 
        self.pack(fill="x", padx=25, pady=2)

        is_done = task_data['completed']
        item_font = ("Segoe UI", 12, "overstrike") if is_done else ("Segoe UI", 12)
        fg_color = Colors.TEXT_DATE if is_done else Colors.TEXT_SUB
        check_char = "☑" if is_done else "☐"

        # Checkbox Toggle
        self.check_btn = tk.Label(self, text=check_char, font=("Segoe UI", 16),
            fg=Colors.PRIMARY if is_done else "#cbd5e0", bg=Colors.BG, width=2, cursor="hand2")
        self.check_btn.pack(side="left")
        self.check_btn.bind("<Button-1>", lambda e: self.callbacks['on_toggle'](task_data['id']))

        # Task Text Label (Double click to edit)
        self.label = tk.Label(self, text=task_data['text'], font=item_font,
            fg=fg_color, bg=Colors.BG, anchor="w", cursor="hand2")
        self.label.pack(side="left", padx=5, fill="x", expand=True)
        self.label.bind("<Double-Button-1>", lambda e: self.callbacks['on_edit'](task_data['id']))

        # Delete Button
        self.del_btn = tk.Label(self, text="✕", font=("Segoe UI", 10), fg="#cbd5e0", bg=Colors.BG, cursor="hand2")
        self.del_btn.pack(side="right", padx=5)
        self.del_btn.bind("<Button-1>", lambda e: self.callbacks['on_delete'](task_data['id']))

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
        self.db = TodoDataManager()

        self.setup_ui()
        self.render_tasks()

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
        self.entry.bind("<Return>", lambda e: self.ui_add())

        tk.Button(input_frame, text="+ Add", command=self.ui_add, bg=Colors.PRIMARY, fg="white", relief="flat", padx=15).pack(side="right")

        # Task Containers
        self.list_area = tk.Frame(self, bg=Colors.BG)
        self.list_area.pack(fill="both", expand=True)

    # --- UI EVENT HANDLERS (Calling the DataManager) ---

    def render_tasks(self):
        """Clears and re-renders the list based on current data."""
        for widget in self.list_area.winfo_children():
            widget.destroy()

        tasks = self.db.get_all_tasks()
        callbacks = {
            'on_toggle': self.ui_toggle,
            'on_edit': self.ui_edit,
            'on_delete': self.ui_delete
        }

        # Render Active
        SectionHeader(self.list_area, "Tasks")
        for t in [t for t in tasks if not t['completed']]:
            TaskItem(self.list_area, t, callbacks)

        # Render Completed
        SectionHeader(self.list_area, "Completed")
        for t in [t for t in tasks if t['completed']]:
            TaskItem(self.list_area, t, callbacks)

    def ui_add(self):
        self.db.add_task(self.entry.get())
        self.entry.delete(0, tk.END)
        self.render_tasks()

    def ui_toggle(self, tid):
        self.db.toggle_task_status(tid)
        self.render_tasks()

    def ui_delete(self, tid):
        if messagebox.askyesno("Delete", "Delete this task?"):
            self.db.delete_task(tid)
            self.render_tasks()

    def ui_edit(self, tid):
        # Find current text for the dialog
        current_task = next(t for t in self.db.get_all_tasks() if t['id'] == tid)
        new_text = simpledialog.askstring("Edit", "Update task:", initialvalue=current_task['text'])
        if new_text:
            self.db.update_task_text(tid, new_text)
            self.render_tasks()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Clean CRUD Architecture")
    root.geometry("400x700")
    TodoModule(root)
    root.mainloop()