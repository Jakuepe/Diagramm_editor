import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox, filedialog
import json
from PIL import ImageGrab

class DiagramEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diagramm-Editor PRO")
        self.geometry("1200x800")

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.boxes = []
        self.connections = []

        self.undo_stack = []
        self.redo_stack = []

        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.connect_mode = False
        self.connect_from_box = None

        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Menü
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Neues Kästchen", command=self.menu_add_box)
        file_menu.add_command(label="Speichern unter...", command=self.menu_save)
        file_menu.add_command(label="Laden...", command=self.menu_load)
        file_menu.add_command(label="Als PNG speichern...", command=self.menu_save_png)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.quit)
        self.menu.add_cascade(label="Datei", menu=file_menu)

        edit_menu = tk.Menu(self.menu, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.menu_undo)
        edit_menu.add_command(label="Redo", command=self.menu_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Text ändern", command=self.menu_change_text)
        edit_menu.add_command(label="Farbe ändern", command=self.menu_change_color)
        edit_menu.add_command(label="Verbindung setzen", command=self.menu_start_connection)
        edit_menu.add_command(label="Verbindung löschen", command=self.menu_delete_connection)
        self.menu.add_cascade(label="Bearbeiten", menu=edit_menu)

        # Events
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-3>", self.handle_right_click)

        self.canvas.bind("<MouseWheel>", self.zoom)  # Windows
        self.canvas.bind("<Button-4>", self.zoom)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)    # Linux scroll down

    # --- Box & Connection ---
    def create_box(self, x, y, text, color):
        box_width = 120
        box_height = 60
        rect = self.canvas.create_rectangle(x, y, x + box_width, y + box_height, fill=color, outline="black", width=2)
        label = self.canvas.create_text(x + box_width / 2, y + box_height / 2, text=text, font=("Arial", 12, "bold"))
        box = {"rect": rect, "label": label}
        self.boxes.append(box)
        self.save_state()
        return box

    def create_connection(self, box1, box2):
        x1, y1 = self.get_box_center(box1)
        x2, y2 = self.get_box_center(box2)
        line = self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, width=2)
        connection = {"line": line, "from": box1, "to": box2}
        self.connections.append(connection)
        self.save_state()

    def get_box_center(self, box):
        coords = self.canvas.coords(box["rect"])
        x_center = (coords[0] + coords[2]) / 2
        y_center = (coords[1] + coords[3]) / 2
        return x_center, y_center

    def find_box_at(self, x, y):
        found = self.canvas.find_closest(x, y)
        if not found or len(found) == 0:
            return None
        item = found[0]
        for box in self.boxes:
            if item == box["rect"] or item == box["label"]:
                return box
        return None

    def find_connection_at(self, x, y):
        found = self.canvas.find_closest(x, y)
        if not found or len(found) == 0:
            return None
        item = found[0]
        for conn in self.connections:
            if conn["line"] == item:
                return conn
        return None

    def get_box_text(self, box):
        return self.canvas.itemcget(box["label"], "text")

    def update_connections(self):
        for conn in self.connections:
            x1, y1 = self.get_box_center(conn["from"])
            x2, y2 = self.get_box_center(conn["to"])
            self.canvas.coords(conn["line"], x1, y1, x2, y2)

    # --- Drag ---
    def start_drag(self, event):
        clicked_box = self.find_box_at(event.x, event.y)
        if clicked_box:
            self.drag_data["item"] = clicked_box
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def do_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            box = self.drag_data["item"]
            self.canvas.move(box["rect"], dx, dy)
            self.canvas.move(box["label"], dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.update_connections()

    def stop_drag(self, event):
        if self.drag_data["item"]:
            self.save_state()
        self.drag_data["item"] = None

    # --- Right Click ---
    def handle_right_click(self, event):
        clicked_box = self.find_box_at(event.x, event.y)
        if clicked_box:
            if messagebox.askyesno("Löschen", f"Kästchen '{self.get_box_text(clicked_box)}' wirklich löschen?"):
                self.delete_box(clicked_box)

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
        self.save_state()

    # --- Zoom ---
    def zoom(self, event):
        factor = 1.1 if event.delta > 0 or event.num == 4 else 0.9
        self.scale_factor *= factor
        self.canvas.scale(tk.ALL, event.x, event.y, factor, factor)
        self.update_connections()

    # --- Undo / Redo ---
    def save_state(self):
        state = {
            "boxes": [],
            "connections": []
        }
        for box in self.boxes:
            coords = self.canvas.coords(box["rect"])
            state["boxes"].append({
                "x": coords[0],
                "y": coords[1],
                "text": self.get_box_text(box),
                "color": self.canvas.itemcget(box["rect"], "fill")
            })
        for conn in self.connections:
            state["connections"].append({
                "from": self.get_box_text(conn["from"]),
                "to": self.get_box_text(conn["to"])
            })
        self.undo_stack.append(json.dumps(state))
        self.redo_stack.clear()

    def load_state(self, state_json):
        state = json.loads(state_json)
        self.canvas.delete(tk.ALL)
        self.boxes.clear()
        self.connections.clear()
        box_lookup = {}
        for box_data in state["boxes"]:
            box = self.create_box(box_data["x"], box_data["y"], box_data["text"], box_data["color"])
            box_lookup[box_data["text"]] = box
        for conn_data in state["connections"]:
            from_box = box_lookup.get(conn_data["from"])
            to_box = box_lookup.get(conn_data["to"])
            if from_box and to_box:
                self.create_connection(from_box, to_box)

    def menu_undo(self):
        if len(self.undo_stack) <= 1:
            return
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        prev_state = self.undo_stack[-1]
        self.load_state(prev_state)
        print("Undo")

    def menu_redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.load_state(state)
        print("Redo")

    # --- Menü-Funktionen ---
    def menu_add_box(self):
        x, y = 100 + len(self.boxes) * 20, 100 + len(self.boxes) * 20
        text = f"Kästchen {len(self.boxes) + 1}"
        color = "lightblue"
        self.create_box(x, y, text, color)

    def menu_change_text(self):
        box = self.select_box_dialog()
        if not box:
            return
        new_text = simpledialog.askstring("Text ändern", "Neuer Text:")
        if new_text:
            self.canvas.itemconfig(box["label"], text=new_text)
            self.save_state()

    def menu_change_color(self):
        box = self.select_box_dialog()
        if not box:
            return
        color = colorchooser.askcolor(title="Farbe wählen")[1]
        if color:
            self.canvas.itemconfig(box["rect"], fill=color)
            self.save_state()

    def menu_start_connection(self):
        box = self.select_box_dialog()
        if not box:
            return
        self.connect_mode = True
        self.connect_from_box = box
        self.canvas.bind("<Button-1>", self.finish_connection)

    def finish_connection(self, event):
        clicked_box = self.find_box_at(event.x, event.y)
        if clicked_box and clicked_box != self.connect_from_box:
            self.create_connection(self.connect_from_box, clicked_box)
        self.connect_mode = False
        self.connect_from_box = None
        self.canvas.bind("<Button-1>", self.start_drag)

    def menu_delete_connection(self):
        messagebox.showinfo("Info", "Klicke auf eine Verbindung, um sie zu löschen.")
        self.canvas.bind("<Button-1>", self._delete_connection_click)

    def _delete_connection_click(self, event):
        conn = self.find_connection_at(event.x, event.y)
        if conn:
            self.canvas.delete(conn["line"])
            self.connections.remove(conn)
            self.save_state()
            print("Verbindung gelöscht.")
        else:
            print("Keine Verbindung an dieser Stelle gefunden.")
        self.canvas.bind("<Button-1>", self.start_drag)

    def select_box_dialog(self):
        if not self.boxes:
            messagebox.showinfo("Info", "Keine Kästchen vorhanden.")
            return None
        box_names = [self.get_box_text(b) for b in self.boxes]
        choice = simpledialog.askstring("Kästchen auswählen", f"Name der Box eingeben:\n{', '.join(box_names)}")
        if not choice:
            return None
        for b in self.boxes:
            if self.get_box_text(b) == choice:
                return b
        messagebox.showwarning("Nicht gefunden", f"'{choice}' wurde nicht gefunden.")
        return None

    def menu_save(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON-Dateien", "*.json")])
        if not file_path:
            return
        state = self.undo_stack[-1]
        with open(file_path, "w") as f:
            f.write(state)
        print(f"Gespeichert als: {file_path}")

    def menu_load(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON-Dateien", "*.json")])
        if not file_path:
            return
        with open(file_path, "r") as f:
            state = f.read()
        self.undo_stack.append(state)
        self.redo_stack.clear()
        self.load_state(state)
        print(f"Geladen: {file_path}")

    def menu_save_png(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG-Bilder", "*.png")])
        if not file_path:
            return
        x = self.winfo_rootx() + self.canvas.winfo_x()
        y = self.winfo_rooty() + self.canvas.winfo_y()
        w = x + self.canvas.winfo_width()
        h = y + self.canvas.winfo_height()
        ImageGrab.grab().crop((x, y, w, h)).save(file_path)
        print(f"PNG gespeichert als: {file_path}")

if __name__ == "__main__":
    app = DiagramEditor()
    app.mainloop()
