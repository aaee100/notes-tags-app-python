

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import uuid
from datetime import datetime

# ---------------------------
# File / storage setup
# ---------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATA_FILE = DATA_DIR / "notes.json"

def ensure_data_file():
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"notes": []}, f, ensure_ascii=False, indent=2)

ensure_data_file()

# ---------------------------
# Timestamp helpers
# ---------------------------
def get_timestamp():
    """Return current timestamp formatted as 'YYYY-MM-DD, HH:MM:SS' (no microseconds)."""
    return datetime.now().replace(microsecond=0).strftime("%Y-%m-%d, %H:%M:%S")

def fix_timestamp(ts):
    """
    Convert various ISO-like timestamps to 'YYYY-MM-DD, HH:MM:SS'.
    Accepts:
      - '2025-10-18T17:05:00'
      - '2025-11-17T16:50:33.774139'
      - '2025-10-18, 17:05:00' (returns unchanged)
    If parsing fails, returns the original string.
    """
    if not ts or not isinstance(ts, str):
        return ts
    ts = ts.strip()
    # already in target format?
    if "," in ts and ":" in ts and "-" in ts and ts.count(",") == 1:
        # try a basic parse to ensure it's valid
        try:
            datetime.strptime(ts, "%Y-%m-%d, %H:%M:%S")
            return ts
        except Exception:
            pass
    # replace space comma variants
    iso = ts.replace(", ", "T") if ", " in ts else ts
    # try parsing with fromisoformat (handles microseconds)
    try:
        dt = datetime.fromisoformat(iso)
        dt = dt.replace(microsecond=0)
        return dt.strftime("%Y-%m-%d, %H:%M:%S")
    except Exception:
        # as fallback, try common patterns
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(iso, fmt)
                return dt.strftime("%Y-%m-%d, %H:%M:%S")
            except Exception:
                pass
    # if all else fails, return original
    return ts

# ---------------------------
# Utilities
# ---------------------------
def normalize_tags(tag_string):
    """Turn comma-separated string into sorted, unique tags list (preserve original casing as entered)."""
    parts = [t.strip() for t in tag_string.split(",") if t.strip()]
    seen = []
    for p in parts:
        pl = p.lower()
        if pl not in [s.lower() for s in seen]:
            seen.append(p)
    return seen

def short_preview(body, length=80):
    first_line = body.splitlines()[0] if body else ""
    preview = (first_line[:length] + "...") if len(first_line) > length else first_line
    return preview

# ---------------------------
# Data functions (load/save) with normalization
# ---------------------------
def load_notes():
    """Load notes and normalize timestamp formats. If normalization changes anything, overwrite file."""
    ensure_data_file()
    changed = False
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = {"notes": []}

    notes = data.get("notes", [])
    for n in notes:
        # ensure id exists
        if "id" not in n or not n.get("id"):
            n["id"] = str(uuid.uuid4())
            changed = True
        # body key backward compatibility: accept 'content' -> 'body'
        if "body" not in n and "content" in n:
            n["body"] = n.pop("content")
            changed = True
        # ensure tags exist and are list
        if "tags" not in n or not isinstance(n["tags"], list):
            tags_raw = n.get("tags", "")
            if isinstance(tags_raw, str):
                n["tags"] = normalize_tags(tags_raw)
            else:
                n["tags"] = []
            changed = True
        # fix created/modified timestamp formats
        created = n.get("created", "")
        modified = n.get("modified", "")
        fixed_created = fix_timestamp(created) if created else get_timestamp()
        fixed_modified = fix_timestamp(modified) if modified else fixed_created
        if fixed_created != created:
            n["created"] = fixed_created
            changed = True
        if fixed_modified != modified:
            n["modified"] = fixed_modified
            changed = True

    if changed:
        save_notes(notes)
    return notes

def save_notes(notes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"notes": notes}, f, ensure_ascii=False, indent=2)

def add_note(title, body, tags_list):
    notes = load_notes()
    ts = get_timestamp()
    note = {
        "id": str(uuid.uuid4()),
        "title": title,
        "body": body,
        "tags": tags_list,
        "created": ts,
        "modified": ts
    }
    notes.append(note)
    save_notes(notes)
    return note

def update_note(note_id, title, body, tags_list):
    notes = load_notes()
    changed = False
    for n in notes:
        if n["id"] == note_id:
            n["title"] = title
            n["body"] = body
            n["tags"] = tags_list
            n["modified"] = get_timestamp()
            changed = True
            break
    if changed:
        save_notes(notes)
    return changed

def delete_note(note_id):
    notes = load_notes()
    new = [n for n in notes if n["id"] != note_id]
    save_notes(new)

# ---------------------------
# App GUI
# ---------------------------
class NotesApp:
    def __init__(self, root):
        self.root = root
        root.title("Notes + Tags App")
        root.geometry("1000x640")

        main = ttk.Frame(root, padding=8)
        main.pack(fill="both", expand=True)

        # Left: Tags list and controls
        left = ttk.Frame(main, width=220)
        left.pack(side="left", fill="y", padx=(0,8))
        ttk.Label(left, text="Tags", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.tag_listbox = tk.Listbox(left, height=20, exportselection=False)
        self.tag_listbox.pack(fill="y", expand=False, pady=6)
        self.tag_listbox.bind("<<ListboxSelect>>", self.on_tag_select)

        ttk.Button(left, text="Clear Tag Filter", command=self.clear_tag_filter).pack(fill="x", pady=(6,3))
        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(left, text="Quick actions").pack(anchor="w")
        ttk.Button(left, text="New Note", command=self.new_note).pack(fill="x", pady=3)
        ttk.Button(left, text="Export Selected (multiple)", command=self.export_selected).pack(fill="x", pady=3)

        # Middle: Notes list + search
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True)

        # Search bar
        search_frame = ttk.Frame(center)
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_notes_list())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6)

        # Notes Treeview (multi-select enabled)
        columns = ("title", "preview", "modified")
        # ensure selectmode="extended" for multi-selection (CTRL/SHIFT)
        self.tree = ttk.Treeview(center, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("title", text="Title")
        self.tree.heading("preview", text="Preview")
        self.tree.heading("modified", text="Modified")
        self.tree.column("title", width=240, anchor="w")
        self.tree.column("preview", width=380, anchor="w")
        self.tree.column("modified", width=180, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(8,0))
        self.tree.bind("<<TreeviewSelect>>", self.on_note_select)

        # Right: Editor
        right = ttk.Frame(main, width=420)
        right.pack(side="right", fill="both", expand=False, padx=(8,0))

        ttk.Label(right, text="Editor", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        editor = ttk.Frame(right)
        editor.pack(fill="both", expand=True, pady=(6,0))

        ttk.Label(editor, text="Title:").pack(anchor="w")
        self.entry_title = ttk.Entry(editor)
        self.entry_title.pack(fill="x", pady=4)

        ttk.Label(editor, text="Tags (comma-separated):").pack(anchor="w")
        self.entry_tags = ttk.Entry(editor)
        self.entry_tags.pack(fill="x", pady=4)

        ttk.Label(editor, text="Body:").pack(anchor="w")
        self.text_body = tk.Text(editor, height=16, wrap="word")
        self.text_body.pack(fill="both", expand=True, pady=4)

        btn_frame = ttk.Frame(editor)
        btn_frame.pack(fill="x", pady=6)
        self.btn_save = ttk.Button(btn_frame, text="Save Note", command=self.save_note)
        self.btn_save.pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete Note", command=self.delete_selected_note).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear Fields", command=self.clear_editor).pack(side="left", padx=2)

        # status bar
        self.status_var = tk.StringVar(value="Data file: notes.json")
        status = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(side="bottom", fill="x")

        # internal state
        self.selected_note_id = None
        self.tag_filter = None  # currently selected tag

        # load initial
        self.refresh_tags()
        self.refresh_notes_list()

    # -------------------------
    # Tag handling
    # -------------------------
    def refresh_tags(self):
        notes = load_notes()
        tags = []
        for n in notes:
            for t in n.get("tags", []):
                if t and t not in tags:
                    tags.append(t)
        tags = sorted(tags, key=lambda x: x.lower())
        self.tag_listbox.delete(0, tk.END)
        for t in tags:
            self.tag_listbox.insert(tk.END, t)

    def on_tag_select(self, event=None):
        sel = None
        try:
            idx = self.tag_listbox.curselection()
            if idx:
                sel = self.tag_listbox.get(idx[0])
        except Exception:
            sel = None
        self.tag_filter = sel
        self.refresh_notes_list()

    def clear_tag_filter(self):
        self.tag_listbox.selection_clear(0, tk.END)
        self.tag_filter = None
        self.refresh_notes_list()

    # -------------------------
    # Notes list / search / filter
    # -------------------------
    def refresh_notes_list(self):
        """Load notes, apply tag + search filters, populate treeview."""
        notes = load_notes()
        q = self.search_var.get().strip().lower()
        filtered = []
        for n in notes:
            title = (n.get("title") or "").lower()
            body = (n.get("body") or "").lower()
            tags = [t.lower() for t in n.get("tags", [])]
            matches_search = (q in title) or (q in body) or (q in " ".join(tags)) if q else True
            matches_tag = (self.tag_filter is None) or (self.tag_filter.lower() in tags)
            if matches_search and matches_tag:
                filtered.append(n)

        # sort by modified desc
        try:
            filtered.sort(key=lambda x: x.get("modified", ""), reverse=True)
        except Exception:
            pass

        # populate tree
        for r in self.tree.get_children():
            self.tree.delete(r)
        for n in filtered:
            preview = short_preview(n.get("body", ""))
            mod = n.get("modified", "")
            # safety: ensure id exists
            iid = n.get("id") or str(uuid.uuid4())
            self.tree.insert("", tk.END, iid=iid, values=(n.get("title",""), preview, mod))

    def on_note_select(self, event=None):
        # If multiple selected, just load the first one
        sel = self.tree.selection()
        if not sel:
            return
        note_id = sel[0]
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return
        self.selected_note_id = note_id
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, note.get("title",""))
        self.entry_tags.delete(0, tk.END)
        self.entry_tags.insert(0, ", ".join(note.get("tags", [])))
        self.text_body.delete("1.0", tk.END)
        self.text_body.insert("1.0", note.get("body",""))

    # -------------------------
    # Editor actions
    # -------------------------
    def clear_editor(self):
        self.selected_note_id = None
        self.entry_title.delete(0, tk.END)
        self.entry_tags.delete(0, tk.END)
        self.text_body.delete("1.0", tk.END)
        # unselect tree
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def new_note(self):
        self.clear_editor()
        self.entry_title.focus_set()

    def save_note(self):
        title = self.entry_title.get().strip()
        body = self.text_body.get("1.0", tk.END).rstrip("\n")
        tags_raw = self.entry_tags.get().strip()
        tags = normalize_tags(tags_raw)

        if not title:
            messagebox.showerror("Validation", "Please provide a title for the note.")
            return

        if self.selected_note_id:
            ok = update_note(self.selected_note_id, title, body, tags)
            if ok:
                self.status_var.set("Note updated.")
            else:
                self.status_var.set("Update failed.")
        else:
            note = add_note(title, body, tags)
            self.selected_note_id = note["id"]
            self.status_var.set("Note added.")

        self.refresh_tags()
        self.refresh_notes_list()

    def delete_selected_note(self):
        if not self.selected_note_id:
            messagebox.showerror("Error", "Select a note to delete (from the list).")
            return
        if not messagebox.askyesno("Confirm", "Delete selected note permanently?"):
            return
        delete_note(self.selected_note_id)
        self.selected_note_id = None
        self.clear_editor()
        self.refresh_tags()
        self.refresh_notes_list()

    # -------------------------
    # Export (multiple)
    # -------------------------
    def export_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select one or more notes to export.")
            return

        # ask for single file to write all selected notes into
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export selected notes as single file"
        )
        if not path:
            return

        notes = load_notes()
        notes_by_id = {n["id"]: n for n in notes}

        try:
            with open(path, "w", encoding="utf-8") as f:
                for iid in selected:
                    n = notes_by_id.get(iid)
                    if not n:
                        continue
                    created = fix_timestamp(n.get("created", ""))
                    modified = fix_timestamp(n.get("modified", ""))
                    f.write(f"Title: {n.get('title','')}\n")
                    f.write(f"Created: {created}\n")
                    f.write(f"Modified: {modified}\n")
                    f.write(f"Tags: {', '.join(n.get('tags', []))}\n\n")
                    f.write(n.get("body",""))
                    f.write("\n\n" + ("-"*60) + "\n\n")
            messagebox.showinfo("Exported", f"Saved {len(selected)} notes to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{e}")

# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()
