"""
Pop-up windows: Save, Open, New Map, questions and error messages.

pygame can't draw normal Windows dialogs, so these use tkinter, which comes
with Python. Each function opens its dialog, waits for an answer and closes.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

MAP_FILE_TYPES = [("Hex maps", "*.json"), ("All files", "*.*")]
MIN_MAP_SIZE = 5
MAX_MAP_SIZE = 200


def _hidden_root():
    """tkinter needs a main window; this one is invisible and stays on top,
    so dialogs don't open hidden behind the editor."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def ask_save_path(folder, suggested_name):
    """Returns the chosen file path, or None if cancelled."""
    root = _hidden_root()
    path = filedialog.asksaveasfilename(
        parent=root, title="Save map", initialdir=folder,
        initialfile=suggested_name + ".json", defaultextension=".json",
        filetypes=MAP_FILE_TYPES)
    root.destroy()
    return path or None


def ask_open_path(folder):
    """Returns the chosen file path, or None if cancelled."""
    root = _hidden_root()
    path = filedialog.askopenfilename(
        parent=root, title="Open map", initialdir=folder, filetypes=MAP_FILE_TYPES)
    root.destroy()
    return path or None


def ask_save_changes(map_name):
    """Unsaved changes: returns True (save), False (don't save) or None (cancel)."""
    root = _hidden_root()
    answer = messagebox.askyesnocancel(
        "Unsaved changes", f'Save changes to "{map_name}" first?', parent=root)
    root.destroy()
    return answer


def show_error(title, message):
    root = _hidden_root()
    messagebox.showerror(title, message, parent=root)
    root.destroy()


def ask_new_map_size(cols, rows):
    """Small window with width and height boxes.
    Returns (cols, rows), or None if cancelled."""
    root = _hidden_root()
    window = tk.Toplevel(root)
    window.title("New map")
    window.resizable(False, False)
    window.attributes("-topmost", True)

    result = {}
    cols_var = tk.IntVar(value=cols)
    rows_var = tk.IntVar(value=rows)

    tk.Label(window, text=f"Map size in hexes ({MIN_MAP_SIZE} to {MAX_MAP_SIZE}):").grid(
        row=0, column=0, columnspan=2, padx=12, pady=(12, 6), sticky="w")
    tk.Label(window, text="Width (columns):").grid(row=1, column=0, padx=12, pady=4, sticky="w")
    tk.Spinbox(window, from_=MIN_MAP_SIZE, to=MAX_MAP_SIZE, textvariable=cols_var, width=8).grid(
        row=1, column=1, padx=12, pady=4)
    tk.Label(window, text="Height (rows):").grid(row=2, column=0, padx=12, pady=4, sticky="w")
    tk.Spinbox(window, from_=MIN_MAP_SIZE, to=MAX_MAP_SIZE, textvariable=rows_var, width=8).grid(
        row=2, column=1, padx=12, pady=4)

    def ok(event=None):
        try:
            c, r = cols_var.get(), rows_var.get()
        except tk.TclError:
            messagebox.showerror("New map", "Please type whole numbers.", parent=window)
            return
        if not (MIN_MAP_SIZE <= c <= MAX_MAP_SIZE and MIN_MAP_SIZE <= r <= MAX_MAP_SIZE):
            messagebox.showerror(
                "New map", f"Sizes must be between {MIN_MAP_SIZE} and {MAX_MAP_SIZE}.", parent=window)
            return
        result["size"] = (c, r)
        window.destroy()

    buttons = tk.Frame(window)
    buttons.grid(row=3, column=0, columnspan=2, pady=12)
    tk.Button(buttons, text="Create", width=10, command=ok).pack(side="left", padx=6)
    tk.Button(buttons, text="Cancel", width=10, command=window.destroy).pack(side="left", padx=6)
    window.bind("<Return>", ok)
    window.bind("<Escape>", lambda event: window.destroy())

    window.focus_force()
    window.grab_set()
    root.wait_window(window)
    root.destroy()
    return result.get("size")


def file_stem(path):
    """'C:/.../MAPS/My Map.json' -> 'My Map'"""
    return os.path.splitext(os.path.basename(path))[0]
