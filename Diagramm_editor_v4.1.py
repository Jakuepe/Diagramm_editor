# --- Diagramm-Editor V4.1 FINAL PRO ---
# MIT Kommentaren und Polygon-Fix!
# Erstellen, bearbeiten und verbinden von Kästchen
# Kontextmenü: Text ändern, Farbe ändern, Form ändern, Löschen
# Undo/Redo, Zoom, PNG-Speichern

import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox, filedialog
import tkinter.ttk as ttk
import json
from PIL import ImageGrab

# --- Hauptklasse ---
class DiagramEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diagramm-Editor V4.1 PRO")
        self.geometry("1200x800")

        # --- Zeichenbereich ---
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # --- Datenstrukturen ---
        self.boxes = []
        self.connections = []

        self.undo_stack = []
        self.redo_stack = []

        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.connect_mode = False
        self.connect_from_box = None
        self.selected_box = None

        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # --- Vorlagen für neue Kästchen ---
        self.box_templates = [
            {"name": "Start", "color": "green", "shape": "oval"},
            {"name": "Prozess", "color": "lightblue", "shape": "rectangle"},
            {"name": "Entscheidung", "color": "orange", "shape": "diamond"},
            {"name": "Ende", "color": "red", "shape": "oval"},
        ]

        # --- Kontextmenü (Rechtsklick) ---
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Text ändern", command=self.menu_change_text)
        self.context_menu.add_command(label="Farbe ändern", command=self.menu_change_color)
        self.context_menu.add_command(label="Form ändern", command=self.menu_change_shape)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Löschen", command=lambda: self.delete_box(self.selected_box))

        # --- Menü ---
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        # --- Datei-Menü ---
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Neues Kästchen (mit Vorlage)", command=self.menu_add_box_with_template)
        file_menu.add_command(label="Neues Kästchen hinzufügen", command=self.menu_add_box)
        file_menu.add_command(label="Neues Diagramm (Strg+N)", command=self.menu_new)
        file_menu.add_separator()
        file_menu.add_command(label="Speichern unter... (Strg+S)", command=self.menu_save)
        file_menu.add_command(label="Laden... (Strg+O)", command=self.menu_load)
        file_menu.add_command(label="Als PNG speichern...", command=self.menu_save_png)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.quit)
        self.menu.add_cascade(label="Datei", menu=file_menu)

        # --- Bearbeiten-Menü ---
        edit_menu = tk.Menu(self.menu, tearoff=0)
        edit_menu.add_command(label="Undo (Strg+Z)", command=self.menu_undo)
        edit_menu.add_command(label="Redo (Strg+Y)", command=self.menu_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Text ändern", command=self.menu_change_text)
        edit_menu.add_command(label="Farbe ändern", command=self.menu_change_color)
        edit_menu.add_command(label="Form ändern", command=self.menu_change_shape)
        edit_menu.add_command(label="Verbindung setzen", command=self.menu_start_connection)
        edit_menu.add_command(label="Verbindung löschen", command=self.menu_delete_connection)
        self.menu.add_cascade(label="Bearbeiten", menu=edit_menu)

        # --- Events ---
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-3>", self.handle_right_click)
        self.canvas.bind("<Double-Button-1>", self.handle_double_click)

        # --- Zoom (Mausrad) ---
        self.canvas.bind("<MouseWheel>", self.zoom)  # Windows
        self.canvas.bind("<Button-4>", self.zoom)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)    # Linux scroll down

        # --- Shortcuts ---
        self.bind("<Control-s>", lambda e: self.menu_save())
        self.bind("<Control-o>", lambda e: self.menu_load())
        self.bind("<Control-z>", lambda e: self.menu_undo())
        self.bind("<Control-y>", lambda e: self.menu_redo())
        self.bind("<Control-n>", lambda e: self.menu_new())
        self.bind("<Control-t>", lambda e: self.menu_add_box_with_template())  # STRG+T → Vorlage

        # --- Initial leeren Zustand speichern (Undo sofort aktiv!) ---
        self.save_state()

# HIER KOMMT DANN TEIL 2 → ALLE METHODS → DIE GANZE LOGIK FÜR BOXEN, VERBINDUNGEN, UNDO/REDO, ETC. → UND GANZ UNTEN DAS MAINLOOP!

    # --- Kontextmenü: Text ändern ---
    def menu_change_text(self):
        if not self.selected_box:
            messagebox.showinfo("Info", "Bitte erst ein Kästchen auswählen.")
            return
        new_text = simpledialog.askstring("Text ändern", "Neuer Text:")
        if new_text:
            self.canvas.itemconfig(self.selected_box["label"], text=new_text)
            self.save_state()

    # --- Kontextmenü: Farbe ändern ---
    def menu_change_color(self):
        if not self.selected_box:
            messagebox.showinfo("Info", "Bitte erst ein Kästchen auswählen.")
            return
        color = colorchooser.askcolor(title="Farbe wählen")[1]
        if color:
            self.canvas.itemconfig(self.selected_box["rect"], fill=color)
            self.save_state()

    # --- Kontextmenü: Form ändern ---
    def menu_change_shape(self):
        if not self.selected_box:
            messagebox.showinfo("Info", "Bitte erst ein Kästchen auswählen.")
            return

        def apply_shape():
            shape_name = combo.get()
            text = self.get_box_text(self.selected_box)
            color = self.canvas.itemcget(self.selected_box["rect"], "fill")
            coords = self.canvas.coords(self.selected_box["rect"])

            # Polygon-Fix: Bounding Box berechnen
            if len(coords) == 4:
                x1, y1, x2, y2 = coords
            else:
                xs = coords[::2]
                ys = coords[1::2]
                x1 = min(xs)
                x2 = max(xs)
                y1 = min(ys)
                y2 = max(ys)

            # Alte Form löschen
            self.canvas.delete(self.selected_box["rect"])

            # Neue Form zeichnen
            if shape_name == "rectangle":
                new_shape = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", width=5)
            elif shape_name == "oval":
                new_shape = self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="black", width=5)
            elif shape_name == "diamond":
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                new_shape = self.canvas.create_polygon(
                    cx, y1, x2, cy, cx, y2, x1, cy,
                    fill=color, outline="black", width=5
                )
            else:
                messagebox.showwarning("Fehler", f"Unbekannte Form: {shape_name}")
                return

            self.selected_box["rect"] = new_shape
            self.select_box(self.selected_box)
            self.update_connections()
            self.save_state()
            win.destroy()

        # --- Dialog ---
        win = tk.Toplevel(self)
        win.title("Form ändern")
        win.geometry("300x100")
        tk.Label(win, text="Neue Form auswählen:").pack(pady=5)

        combo = ttk.Combobox(win, values=["rectangle", "oval", "diamond"])
        combo.pack(pady=5)
        combo.current(0)

        tk.Button(win, text="OK", command=apply_shape).pack(pady=5)

    # --- Menü: Neues Kästchen mit Vorlage ---
    def menu_add_box_with_template(self):
        def create_selected():
            index = combo.current()
            if index >= 0:
                tpl = self.box_templates[index]
                self.create_box_with_shape(100 + len(self.boxes) * 20, 100 + len(self.boxes) * 20, tpl)
            win.destroy()

        win = tk.Toplevel(self)
        win.title("Neues Kästchen auswählen")
        win.geometry("300x100")
        tk.Label(win, text="Vorlage auswählen:").pack(pady=5)

        combo = ttk.Combobox(win, values=[tpl["name"] for tpl in self.box_templates])
        combo.pack(pady=5)
        combo.current(0)

        tk.Button(win, text="OK", command=create_selected).pack(pady=5)

    # --- Menü: Neues Kästchen hinzufügen ---
    def menu_add_box(self):
        x, y = 100 + len(self.boxes) * 20, 100 + len(self.boxes) * 20
        text = f"Kästchen {len(self.boxes) + 1}"
        color = "lightblue"
        self.create_box(x, y, text, color)

    # --- Menü: Neues Diagramm ---
    def menu_new(self):
        if messagebox.askyesno("Neu", "Ungespeicherte Änderungen gehen verloren. Neues Diagramm erstellen?"):
            self.canvas.delete(tk.ALL)
            self.boxes.clear()
            self.connections.clear()
            self.selected_box = None
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()

    # --- Menü: Verbindung setzen ---
    def menu_start_connection(self):
        if not self.selected_box:
            messagebox.showinfo("Info", "Bitte erst ein Kästchen auswählen.")
            return
        self.connect_mode = True
        self.connect_from_box = self.selected_box
        self.canvas.bind("<Button-1>", self.finish_connection)

    def finish_connection(self, event):
        clicked_box = self.find_box_at(event.x, event.y)
        if clicked_box and clicked_box != self.connect_from_box:
            self.create_connection(self.connect_from_box, clicked_box)
        self.connect_mode = False
        self.connect_from_box = None
        self.canvas.bind("<Button-1>", self.start_drag)

    # --- Menü: Verbindung löschen ---
    def menu_delete_connection(self):
        messagebox.showinfo("Info", "Klicke auf eine Verbindung, um sie zu löschen.")
        self.canvas.bind("<Button-1>", self._delete_connection_click)

    def _delete_connection_click(self, event):
        conn = self.find_connection_at(event.x, event.y)
        if conn:
            self.canvas.delete(conn["line"])
            self.connections.remove(conn)
            self.save_state()
        self.canvas.bind("<Button-1>", self.start_drag)

    # --- Menü: Kästchen löschen ---
    def delete_box(self, box):
        to_remove = []
        for conn in self.connections:
            if conn["from"] == box or conn["to"] == box:
                self.canvas.delete(conn["line"])
                to_remove.append(conn)
        for conn in to_remove:
            self.connections.remove(conn)
        self.canvas.delete(box["rect"])
        self.canvas.delete(box["label"])
        self.boxes.remove(box)
        self.selected_box = None
        self.save_state()

    # --- Menü: Undo ---
    def menu_undo(self):
        if len(self.undo_stack) <= 1:
            return
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        prev_state = self.undo_stack[-1]
        self.load_state(prev_state)

    # --- Menü: Redo ---
    def menu_redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.load_state(state)
    # --- Menü: Speichern unter (JSON) ---
    def menu_save(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON-Dateien", "*.json")])
        if not file_path:
            return
        state = self.undo_stack[-1]
        with open(file_path, "w") as f:
            f.write(state)

    # --- Menü: Laden (JSON) ---
    def menu_load(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON-Dateien", "*.json")])
        if not file_path:
            return
        with open(file_path, "r") as f:
            state = f.read()
        self.undo_stack.append(state)
        self.redo_stack.clear()
        self.load_state(state)

    # --- Menü: Speichern als PNG ---
    def menu_save_png(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG-Bilder", "*.png")])
        if not file_path:
            return
        x = self.winfo_rootx() + self.canvas.winfo_x()
        y = self.winfo_rooty() + self.canvas.winfo_y()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()
        ImageGrab.grab().crop((x, y, w, h)).save(file_path)

# --- Hauptprogramm ---
if __name__ == "__main__":
    app = DiagramEditor()
    app.mainloop()
