import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QGraphicsScene,
    QGraphicsView, QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem,
    QMenu, QColorDialog, QInputDialog, QMessageBox, QDialog,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF


def get_edge_point(item, other_center):
    rect = item.sceneBoundingRect()
    center = rect.center()
    line = QLineF(center, other_center)

    # Vier Kanten des Rechtecks als Linien definieren
    rect_edges = [
        QLineF(rect.topLeft(), rect.topRight()),
        QLineF(rect.bottomLeft(), rect.bottomRight()),
        QLineF(rect.topLeft(), rect.bottomLeft()),
        QLineF(rect.topRight(), rect.bottomRight())
    ]

    for edge in rect_edges:
        intersect_point = QPointF()
        intersect_type = line.intersect(edge, intersect_point)
        if intersect_type == QLineF.BoundedIntersection:
            return intersect_point

    # Fallback: Mittelpunkt
    return center


class DiagramItem(QGraphicsItem):
    def __init__(self, shape="rectangle", width=100, height=50,
                 fill_colors=(Qt.white, Qt.white), border_color=Qt.black,
                 texts=("", "")):
        super().__init__()
        self.shape = shape
        self.width = width
        self.height = height
        self.fill_color_top = QColor(fill_colors[0])
        self.fill_color_bottom = QColor(fill_colors[1])
        self.border_color = QColor(border_color)
        self.texts = list(texts)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.edges = []

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        pen = QPen(self.border_color)
        pen.setWidth(2)
        painter.setPen(pen)

        rect = QRectF(0, 0, self.width, self.height)
        if self.shape == "rectangle":
            top_rect = QRectF(0, 0, self.width, self.height / 2)
            bottom_rect = QRectF(0, self.height / 2, self.width, self.height / 2)
            painter.setBrush(QBrush(self.fill_color_top))
            painter.drawRect(top_rect)
            painter.setBrush(QBrush(self.fill_color_bottom))
            painter.drawRect(bottom_rect)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
        elif self.shape == "ellipse":
            painter.save()
            painter.setClipRect(QRectF(0, 0, self.width, self.height / 2))
            painter.setBrush(QBrush(self.fill_color_top))
            painter.drawEllipse(rect)
            painter.restore()
            painter.save()
            painter.setClipRect(QRectF(0, self.height / 2, self.width, self.height / 2))
            painter.setBrush(QBrush(self.fill_color_bottom))
            painter.drawEllipse(rect)
            painter.restore()
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
        elif self.shape == "triangle":
            A = QPointF(self.width / 2, 0)
            B = QPointF(self.width, self.height)
            C = QPointF(0, self.height)
            midpoint_AB = QPointF((A.x() + B.x()) / 2, (A.y() + B.y()) / 2)
            midpoint_AC = QPointF((A.x() + C.x()) / 2, (A.y() + C.y()) / 2)
            top_poly = [A, midpoint_AB, midpoint_AC]
            painter.setBrush(QBrush(self.fill_color_top))
            painter.drawPolygon(*top_poly)
            bottom_poly = [midpoint_AC, midpoint_AB, B, C]
            painter.setBrush(QBrush(self.fill_color_bottom))
            painter.drawPolygon(*bottom_poly)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(A, B, C)
        else:
            top_rect = QRectF(0, 0, self.width, self.height / 2)
            bottom_rect = QRectF(0, self.height / 2, self.width, self.height / 2)
            painter.setBrush(QBrush(self.fill_color_top))
            painter.drawRect(top_rect)
            painter.setBrush(QBrush(self.fill_color_bottom))
            painter.drawRect(bottom_rect)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

        painter.setPen(Qt.black)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect.adjusted(5, 5, -5, -self.height / 2),
                         Qt.AlignLeft | Qt.AlignTop, self.texts[0])
        painter.drawText(rect.adjusted(5, self.height / 2, -5, -5),
                         Qt.AlignLeft | Qt.AlignTop, self.texts[1])

    def contextMenuEvent(self, event):
        scene = self.scene()
        if scene.connect_mode:
            return
        menu = QMenu()
        change_shape = menu.addAction("Form ändern")
        change_fill_top = menu.addAction("Obere Farbe ändern")
        change_fill_bottom = menu.addAction("Untere Farbe ändern")
        change_border = menu.addAction("Rahmenfarbe ändern")
        edit_text1 = menu.addAction("Textzeile 1 ändern")
        edit_text2 = menu.addAction("Textzeile 2 ändern")
        connect_action = menu.addAction("Verbindung erstellen")
        save_shape = menu.addAction("Form speichern")

        action = menu.exec_(event.screenPos())
        if action == change_shape:
            shapes = ["rectangle", "ellipse", "triangle"]
            shape, ok = QInputDialog.getItem(None, "Form wählen", "Form:", shapes, 0, False)
            if ok:
                self.shape = shape
                self.update()
        elif action == change_fill_top:
            color = QColorDialog.getColor(self.fill_color_top)
            if color.isValid():
                self.fill_color_top = color
                self.update()
        elif action == change_fill_bottom:
            color = QColorDialog.getColor(self.fill_color_bottom)
            if color.isValid():
                self.fill_color_bottom = color
                self.update()
        elif action == change_border:
            color = QColorDialog.getColor(self.border_color)
            if color.isValid():
                self.border_color = color
                self.update()
        elif action == edit_text1:
            text, ok = QInputDialog.getText(None, "Textzeile 1", "Text:", text=self.texts[0])
            if ok:
                self.texts[0] = text
                self.update()
        elif action == edit_text2:
            text, ok = QInputDialog.getText(None, "Textzeile 2", "Text:", text=self.texts[1])
            if ok:
                self.texts[1] = text
                self.update()
        elif action == connect_action:
            scene.start_connection(self)
        elif action == save_shape:
            scene.save_shape_to_library(self)

    def add_edge(self, edge):
        self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def to_dict(self):
        return {
            "shape": self.shape,
            "x": self.x(),
            "y": self.y(),
            "width": self.width,
            "height": self.height,
            "fill_color_top": self.fill_color_top.name(),
            "fill_color_bottom": self.fill_color_bottom.name(),
            "border_color": self.border_color.name(),
            "texts": self.texts,
        }

    @staticmethod
    def from_dict(data):
        item = DiagramItem(
            shape=data.get("shape", "rectangle"),
            width=data.get("width", 100),
            height=data.get("height", 50),
            fill_colors=(data.get("fill_color_top", "#ffffff"), data.get("fill_color_bottom", "#ffffff")),
            border_color=data.get("border_color", "#000000"),
            texts=tuple(data.get("texts", ("", "")))
        )
        item.setPos(data.get("x", 0), data.get("y", 0))
        return item


class Edge(QGraphicsLineItem):
    def __init__(self, source, dest, style="solid", label=""):
        super().__init__()
        self.source = source
        self.dest = dest
        self.style = style
        self.label_text = label
        self.setZValue(-1)

        pen = QPen(Qt.black)
        pen.setWidth(2)
        self.setPen(pen)

        self.source.add_edge(self)
        self.dest.add_edge(self)

        self.text_item = QGraphicsTextItem(self.label_text, self)
        font = QFont()
        font.setPointSize(8)
        self.text_item.setFont(font)

        self.update_style()
        self.update_position()

    def update_position(self):
        source_center = self.source.sceneBoundingRect().center()
        dest_center = self.dest.sceneBoundingRect().center()

        p1 = get_edge_point(self.source, dest_center)
        p2 = get_edge_point(self.dest, source_center)

        self.setLine(QLineF(p1, p2))
        mid = QLineF(p1, p2).pointAt(0.5)
        self.text_item.setPos(mid.x(), mid.y())

    def update_style(self):
        pen = self.pen()
        if self.style == "solid":
            pen.setStyle(Qt.SolidLine)
        elif self.style == "dashed":
            pen.setStyle(Qt.DashLine)
        elif self.style == "dotted":
            pen.setStyle(Qt.DotLine)
        else:
            pen.setStyle(Qt.SolidLine)
        self.setPen(pen)

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_style = menu.addAction("Linienstil ändern")
        edit_label = menu.addAction("Beschriftung ändern")
        action = menu.exec_(event.screenPos())

        if action == change_style:
            styles = ["solid", "dashed", "dotted"]
            style, ok = QInputDialog.getItem(None, "Linienstil wählen", "Stil:", styles, 0, False)
            if ok:
                self.style = style
                self.update_style()

        elif action == edit_label:
            text, ok = QInputDialog.getText(None, "Verbindungstext", "Text:", text=self.label_text)
            if ok:
                self.label_text = text
                self.text_item.setPlainText(text)

    def to_dict(self):
        return {
            "source_index": self.source_index,
            "dest_index": self.dest_index,
            "style": self.style,
            "label": self.label_text,
        }

    def set_indices(self, source_index, dest_index):
        self.source_index = source_index
        self.dest_index = dest_index

    @staticmethod
    def from_dict(data, items):
        source = items[data["source_index"]]
        dest = items[data["dest_index"]]
        edge = Edge(source, dest, style=data.get("style", "solid"), label=data.get("label", ""))
        return edge


class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.temp_edge = None
        self.start_item = None
        self.saved_shapes = []
        self.connect_mode = False
        self.connect_source = None

    def mousePressEvent(self, event):
        if self.connect_mode:
            items = self.items(event.scenePos())
            for item in items:
                if isinstance(item, DiagramItem):
                    if not self.connect_source:
                        self.connect_source = item
                    else:
                        if item is not self.connect_source:
                            edge = Edge(self.connect_source, item)
                            self.addItem(edge)
                        self.connect_mode = False
                        self.connect_source = None
                    return
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        if self.connect_mode:
            return

        items = self.items(event.scenePos())
        if not items:
            menu = QMenu()
            add_box = menu.addAction("Neues Kästchen hinzufügen")
            saved_action = menu.addAction("Gespeicherte Form hinzufügen") if self.saved_shapes else None
            action = menu.exec_(event.screenPos())

            if action == add_box:
                item = DiagramItem()
                item.setPos(event.scenePos())
                self.addItem(item)

            elif action == saved_action:
                sub_menu = QMenu()
                actions = []
                for idx, shape_data in enumerate(self.saved_shapes):
                    a = sub_menu.addAction(shape_data["name"])
                    actions.append((a, idx))
                chosen = sub_menu.exec_(event.screenPos())

                for act, idx in actions:
                    if act == chosen:
                        data = self.saved_shapes[idx]["data"]
                        item = DiagramItem.from_dict(data)
                        item.setPos(event.scenePos())
                        self.addItem(item)
                        break
        else:
            super().contextMenuEvent(event)

    def start_connection(self, source_item):
        self.connect_mode = True
        self.connect_source = source_item

    def save_shape_to_library(self, item):
        name, ok = QInputDialog.getText(None, "Name der Form", "Name:")
        if ok and name:
            data = item.to_dict()
            self.saved_shapes.append({"name": name, "data": data})

    def clear(self):
        super().clear()

    def to_dict(self):
        items = [item for item in self.items() if isinstance(item, DiagramItem)]
        item_list = []
        for item in items:
            item_list.append(item.to_dict())

        for idx, item in enumerate(items):
            item._index = idx

        edges = [item for item in self.items() if isinstance(item, Edge)]
        edge_list = []
        for edge in edges:
            edge.set_indices(edge.source._index, edge.dest._index)
            edge_list.append(edge.to_dict())

        return {"items": item_list, "edges": edge_list, "saved_shapes": self.saved_shapes}

    def from_dict(self, data):
        self.clear()
        self.saved_shapes = data.get("saved_shapes", [])
        item_objs = []
        for item_data in data.get("items", []):
            item = DiagramItem.from_dict(item_data)
            self.addItem(item)
            item_objs.append(item)
        for edge_data in data.get("edges", []):
            edge = Edge.from_dict(edge_data, item_objs)
            self.addItem(edge)

    def export_table(self, filename):
        items = [item for item in self.items() if isinstance(item, DiagramItem)]
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\"Kästchen Text\",\"Verbunden mit\"\n")
            for item in items:
                connections = []
                for edge in item.edges:
                    other = edge.dest if edge.source is item else edge.source
                    connections.append("/".join(other.texts))
                line = f"\"{'/'.join(item.texts)}\",\"{';'.join(connections)}\"\n"
                f.write(line)

    def show_table_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("Tabelle der Kästchen und Verbindungen")
        layout = QVBoxLayout()
        table = QTableWidget()
        items = [item for item in self.items() if isinstance(item, DiagramItem)]
        table.setRowCount(len(items))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Kästchen Text", "Verbunden mit"])

        for row, item in enumerate(items):
            text_item = "/".join(item.texts)
            connections = []
            for edge in item.edges:
                other = edge.dest if edge.source is item else edge.source
                connections.append("/".join(other.texts))
            conn_text = ";".join(connections)
            table.setItem(row, 0, QTableWidgetItem(text_item))
            table.setItem(row, 1, QTableWidgetItem(conn_text))

        layout.addWidget(table)
        btn_export = QPushButton("Tabelle exportieren")
        layout.addWidget(btn_export)
        btn_export.clicked.connect(lambda: self.export_table_dialog())
        dialog.setLayout(layout)
        dialog.resize(400, 300)
        dialog.exec_()

    def export_table_dialog(self):
        filename, _ = QFileDialog.getSaveFileName(None, "Tabelle speichern", "", "CSV-Datei (*.csv)")
        if filename:
            self.export_table(filename)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramm-Editor")
        self.resize(800, 600)
        self.scene = DiagramScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        self.create_actions()
        self.create_menus()
        self.create_toolbar()

    def create_actions(self):
        self.new_action = QAction("Neue Seite", self)
        self.new_action.triggered.connect(self.new_page)
        self.save_action = QAction("Speichern", self)
        self.save_action.triggered.connect(self.save_diagram)
        self.load_action = QAction("Laden", self)
        self.load_action.triggered.connect(self.load_diagram)
        self.export_png_action = QAction("Als PNG exportieren", self)
        self.export_png_action.triggered.connect(self.export_png)
        self.export_pdf_action = QAction("Als PDF exportieren", self)
        self.export_pdf_action.triggered.connect(self.export_pdf)
        self.show_table_action = QAction("Tabelle anzeigen", self)
        self.show_table_action.triggered.connect(self.scene.show_table_dialog)
        self.new_box_action = QAction("Neues Kästchen", self)
        self.new_box_action.triggered.connect(self.add_new_box)
        self.connect_mode_action = QAction("Verbindung erstellen", self)
        self.connect_mode_action.setCheckable(True)
        self.connect_mode_action.triggered.connect(self.toggle_connect_mode)

    def create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Datei")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.load_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_png_action)
        file_menu.addAction(self.export_pdf_action)

        insert_menu = menu_bar.addMenu("Einfügen")
        insert_menu.addAction(self.new_box_action)
        insert_menu.addAction(self.connect_mode_action)

        view_menu = menu_bar.addMenu("Ansicht")
        view_menu.addAction(self.show_table_action)

    def create_toolbar(self):
        toolbar = self.addToolBar("Werkzeugleiste")
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.load_action)
        toolbar.addAction(self.new_box_action)
        toolbar.addAction(self.connect_mode_action)
        toolbar.addAction(self.export_png_action)
        toolbar.addAction(self.export_pdf_action)
        toolbar.addAction(self.show_table_action)

    def new_page(self):
        confirm = QMessageBox.question(self, "Neue Seite",
            "Wirklich neue Seite erstellen? Nicht gespeicherte Änderungen gehen verloren.",
            QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.scene.clear()

    def save_diagram(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Diagramm speichern", "", "Diagramm-Datei (*.json)")
        if filename:
            data = self.scene.to_dict()
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def load_diagram(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "Diagramm-Datei (*.json)")
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.scene.from_dict(data)

    def add_new_box(self):
        center_point = self.view.mapToScene(self.view.viewport().rect().center())
        item = DiagramItem()
        item.setPos(center_point)
        self.scene.addItem(item)

    def toggle_connect_mode(self, checked):
        self.scene.connect_mode = checked
        if not checked:
            self.scene.connect_source = None

    def export_png(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Als PNG speichern", "", "PNG-Datei (*.png)")
        if filename:
            rect = self.scene.itemsBoundingRect()
            image = QPixmap(rect.size().toSize())
            image.fill(Qt.white)
            painter = QPainter(image)
            self.scene.render(painter, QRectF(image.rect()), rect)
            painter.end()
            image.save(filename, "PNG")

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Als PDF speichern", "", "PDF-Datei (*.pdf)")
        if filename:
            from PyQt5.QtPrintSupport import QPrinter
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            painter = QPainter(printer)
            rect = self.scene.itemsBoundingRect()
            self.scene.render(painter, QRectF(printer.pageRect()), rect)
            painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
