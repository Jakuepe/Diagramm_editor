import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QFileDialog, QToolBar, QAction, QColorDialog, QInputDialog,
    QListWidget, QListWidgetItem, QDockWidget, QMessageBox, QMenu,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QFont, QPainter, QImage, QTransform,
    QPolygonF, QPixmap, QIcon
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QPoint

TEMPLATES_FILE = "templates.json"


class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", rect=QRectF(0, 0, 100, 60), text1="Node", text2="", color=QColor("lightgray")):
        # Höhe auf 60 gesetzt, um zwei Textzeilen unterzubringen
        super().__init__(rect)
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.shape = shape
        self.brush = QBrush(color)
        self.pen = QPen(Qt.black)
        self.setBrush(self.brush)
        self.setPen(self.pen)

        self.text1 = text1
        self.text2 = text2

        self.text_item1 = QGraphicsTextItem(text1, self)
        self.text_item1.setDefaultTextColor(Qt.black)
        font1 = QFont()
        font1.setPointSize(10)
        self.text_item1.setFont(font1)

        self.text_item2 = QGraphicsTextItem(text2, self)
        self.text_item2.setDefaultTextColor(Qt.black)
        font2 = QFont()
        font2.setPointSize(8)
        self.text_item2.setFont(font2)

        self.center_texts()

    def center_texts(self):
        rect = self.rect()
        # Textzeile 1 zentrieren
        text1_rect = self.text_item1.boundingRect()
        x1 = rect.x() + (rect.width() - text1_rect.width()) / 2
        y1 = rect.y() + 5
        self.text_item1.setPos(x1, y1)
        # Textzeile 2 direkt unter Zeile 1
        text2_rect = self.text_item2.boundingRect()
        x2 = rect.x() + (rect.width() - text2_rect.width()) / 2
        y2 = y1 + text1_rect.height()
        self.text_item2.setPos(x2, y2)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        r = self.rect()
        if self.shape == "rect":
            painter.drawRect(r)
        elif self.shape == "ellipse":
            painter.drawEllipse(r)
        elif self.shape == "diamond":
            points = [
                QPointF(r.x() + r.width() / 2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height() / 2),
                QPointF(r.x() + r.width() / 2, r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height() / 2)
            ]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape == "triangle":
            points = [
                QPointF(r.x() + r.width() / 2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height())
            ]
            painter.drawPolygon(QPolygonF(points))
        elif self.shape == "hexagon":
            w, h = r.width(), r.height()
            x, y = r.x(), r.y()
            points = [
                QPointF(x + w * 0.25, y),
                QPointF(x + w * 0.75, y),
                QPointF(x + w, y + h / 2),
                QPointF(x + w * 0.75, y + h),
                QPointF(x + w * 0.25, y + h),
                QPointF(x, y + h / 2)
            ]
            painter.drawPolygon(QPolygonF(points))
        self.center_texts()

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        change_shape = menu.addAction("Form ändern")
        connect_node = menu.addAction("Verbinden")
        edit_text = menu.addAction("Text bearbeiten")
        delete_node = menu.addAction("Löschen")
        action = menu.exec_(event.screenPos())
        if action == change_color:
            color = QColorDialog.getColor(self.brush.color())
            if color.isValid():
                self.brush.setColor(color)
                self.update()
        elif action == change_shape:
            shapes = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
            idx, ok = QInputDialog.getItem(None, "Form wählen", "Form:", shapes, 0, False)
            if ok:
                mapping = {
                    "Rechteck": "rect",
                    "Ellipse": "ellipse",
                    "Raute": "diamond",
                    "Dreieck": "triangle",
                    "Hexagon": "hexagon"
                }
                self.shape = mapping[idx]
                self.update()
        elif action == connect_node:
            # Verbindung initiieren: nächster Klick wird Ziel
            self.scene().connecting = True
            self.scene().connect_source = self
        elif action == edit_text:
            # Zwei Zeilen abfragen
            text1, ok1 = QInputDialog.getText(None, "Primärer Text", "Textzeile 1:", text=self.text1)
            if ok1:
                text2, ok2 = QInputDialog.getText(None, "Sekundärer Text", "Textzeile 2:", text=self.text2)
                if ok2:
                    self.text1 = text1
                    self.text2 = text2
                    self.text_item1.setPlainText(text1)
                    self.text_item2.setPlainText(text2)
                    self.center_texts()
                    # Tabelle aktualisieren
                    self.scene().parent.update_table()
        elif action == delete_node:
            # Entferne Knoten und alle Kanten, aktualisiere Tabelle
            for edge in list(self.scene().items()):
                if isinstance(edge, EdgeItem) and (edge.source == self or edge.dest == self):
                    self.scene().removeItem(edge)
                    self.scene().edges.remove(edge)
            self.scene().removeItem(self)
            self.scene().nodes.remove(self)
            self.scene().parent.update_table()
        super().contextMenuEvent(event)


class EdgeItem(QGraphicsLineItem):
    def __init__(self, source: NodeItem, dest: NodeItem, line_style=Qt.SolidLine):
        super().__init__()
        self.source = source
        self.dest = dest
        self.pen = QPen(Qt.black, 2)
        self.pen.setStyle(line_style)
        self.setPen(self.pen)
        self.update_position()
        self.setZValue(-1)

    def update_position(self):
        src_c = self.source.sceneBoundingRect().center()
        dest_c = self.dest.sceneBoundingRect().center()
        self.setLine(src_c.x(), src_c.y(), dest_c.x(), dest_c.y())

    def paint(self, painter, option, widget):
        self.update_position()
        painter.setPen(self.pen)
        painter.drawLine(self.line())

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_edge = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        if action == delete_edge:
            self.scene().removeItem(self)
            self.scene().edges.remove(self)
            # Tabelle aktualisieren
            self.scene().parent.update_table()
        super().contextMenuEvent(event)


class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.connecting = False
        self.connect_source = None
        self.parent = None  # Wird auf MainWindow referenzieren

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if self.connecting and event.button() == Qt.LeftButton and isinstance(item, NodeItem):
            dest = item
            styles = ["Durchgezogen", "Gestrichelt", "Gepunktet"]
            style_str, ok = QInputDialog.getItem(None, "Linienstil wählen", "Stil:", styles, 0, False)
            if ok:
                mapping = {
                    "Durchgezogen": Qt.SolidLine,
                    "Gestrichelt": Qt.DashLine,
                    "Gepunktet": Qt.DotLine
                }
                line_style = mapping[style_str]
            else:
                line_style = Qt.SolidLine
            edge = EdgeItem(self.connect_source, dest, line_style)
            self.addItem(edge)
            self.edges.append(edge)
            self.connecting = False
            self.connect_source = None
            self.parent.update_table()
        else:
            super().mousePressEvent(event)


class Template:
    def __init__(self, name, shape, color, width, height, text1, text2):
        self.name = name
        self.shape = shape
        self.color = color
        self.width = width
        self.height = height
        self.text1 = text1
        self.text2 = text2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramm-Editor")
        self.setGeometry(100, 100, 1000, 600)

        self.scene = DiagramScene()
        self.scene.parent = self
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.templates = []
        self.load_templates()
        self.init_ui()
        self.update_table()

    def init_ui(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_node_action = QAction("Knoten hinzufügen", self)
        add_node_action.triggered.connect(self.add_node)
        toolbar.addAction(add_node_action)

        new_page_action = QAction("Neue Seite", self)
        new_page_action.triggered.connect(self.new_page)
        toolbar.addAction(new_page_action)

        save_action = QAction("Speichern", self)
        save_action.triggered.connect(self.save_diagram)
        toolbar.addAction(save_action)

        load_action = QAction("Laden", self)
        load_action.triggered.connect(self.load_diagram)
        toolbar.addAction(load_action)

        export_img_action = QAction("Als Bild exportieren", self)
        export_img_action.triggered.connect(self.export_image)
        toolbar.addAction(export_img_action)

        export_pdf_action = QAction("Als PDF exportieren", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        toolbar.addAction(export_pdf_action)

        export_table_action = QAction("Tabelle exportieren", self)
        export_table_action.triggered.connect(self.export_table)
        toolbar.addAction(export_table_action)

        create_template_action = QAction("Template erstellen", self)
        create_template_action.triggered.connect(self.create_template)
        toolbar.addAction(create_template_action)

        delete_template_action = QAction("Template löschen", self)
        delete_template_action.triggered.connect(self.delete_template)
        toolbar.addAction(delete_template_action)

        # Template-Liste rechts
        self.template_list = QListWidget()
        self.template_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_list.customContextMenuRequested.connect(self.show_template_context_menu)
        for tpl in self.templates:
            item = self.create_template_item(tpl)
            self.template_list.addItem(item)
        self.template_list.itemDoubleClicked.connect(self.add_node_from_template)
        template_dock = QDockWidget("Templates", self)
        template_dock.setWidget(self.template_list)
        self.addDockWidget(Qt.RightDockWidgetArea, template_dock)

        # Tabelle rechts unten
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Text1", "Text2", "Form", "Farbe"])
        table_dock = QDockWidget("Tabelle", self)
        table_dock.setWidget(self.table)
        self.addDockWidget(Qt.RightDockWidgetArea, table_dock)

    def create_template_item(self, tpl):
        item = QListWidgetItem(tpl.name)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        brush = QBrush(QColor(tpl.color))
        pen = QPen(Qt.black)
        painter.setBrush(brush)
        painter.setPen(pen)
        if tpl.shape == "rect":
            painter.drawRect(4, 8, 24, 16)
        elif tpl.shape == "ellipse":
            painter.drawEllipse(4, 8, 24, 16)
        elif tpl.shape == "diamond":
            points = [QPointF(16, 2), QPointF(30, 16), QPointF(16, 30), QPointF(2, 16)]
            painter.drawPolygon(QPolygonF(points))
        elif tpl.shape == "triangle":
            points = [QPointF(16, 2), QPointF(30, 30), QPointF(2, 30)]
            painter.drawPolygon(QPolygonF(points))
        elif tpl.shape == "hexagon":
            points = [
                QPointF(8, 2), QPointF(24, 2), QPointF(30, 16),
                QPointF(24, 30), QPointF(8, 30), QPointF(2, 16)
            ]
            painter.drawPolygon(QPolygonF(points))
        painter.end()
        item.setIcon(QIcon(pixmap))
        return item

    def show_template_context_menu(self, pos):
        item = self.template_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        delete_action = menu.addAction("Template löschen")
        action = menu.exec_(self.template_list.mapToGlobal(pos))
        if action == delete_action:
            row = self.template_list.row(item)
            del self.templates[row]
            self.template_list.takeItem(row)
            self.save_templates()

    def add_node(self):
        node = NodeItem()
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
        self.scene.nodes.append(node)
        self.update_table()

    def add_node_from_template(self, item: QListWidgetItem):
        name = item.text()
        tpl = next((t for t in self.templates if t.name == name), None)
        if tpl:
            node = NodeItem(
                shape=tpl.shape,
                rect=QRectF(0, 0, tpl.width, tpl.height),
                text1=tpl.text1,
                text2=tpl.text2,
                color=QColor(tpl.color)
            )
            node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
            self.update_table()

    def new_page(self):
        # Szene leeren
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        # Tabelle leeren
        self.table.setRowCount(0)

    def save_diagram(self):
        path, _ = QFileDialog.getSaveFileName(self, "Diagramm speichern", "", "JSON-Datei (*.json)")
        if not path:
            return
        data = {"nodes": [], "edges": []}
        for idx, node in enumerate(self.scene.nodes):
            data["nodes"].append({
                "id": idx,
                "shape": node.shape,
                "color": node.brush.color().name(),
                "x": node.pos().x(),
                "y": node.pos().y(),
                "width": node.rect().width(),
                "height": node.rect().height(),
                "text1": node.text1,
                "text2": node.text2
            })
        for edge in self.scene.edges:
            src_id = self.scene.nodes.index(edge.source)
            dest_id = self.scene.nodes.index(edge.dest)
            style = edge.pen.style()
            data["edges"].append({"source": src_id, "dest": dest_id, "style": style})
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Gespeichert", "Diagramm wurde gespeichert.")

    def load_diagram(self):
        path, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "JSON-Datei (*.json)")
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)
        # Szene leeren
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        # Knoten laden
        for node_data in data.get("nodes", []):
            node = NodeItem(
                shape=node_data.get("shape", "rect"),
                rect=QRectF(0, 0, node_data.get("width", 100), node_data.get("height", 60)),
                text1=node_data.get("text1", ""),
                text2=node_data.get("text2", ""),
                color=QColor(node_data.get("color", "lightgray"))
            )
            node.setPos(node_data.get("x", 0), node_data.get("y", 0))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
        # Verbindungen laden
        for edge_data in data.get("edges", []):
            src = self.scene.nodes[edge_data.get("source")]
            dest = self.scene.nodes[edge_data.get("dest")]
            style = edge_data.get("style", Qt.SolidLine)
            edge = EdgeItem(src, dest, style)
            self.scene.addItem(edge)
            self.scene.edges.append(edge)
        self.update_table()
        QMessageBox.information(self, "Geladen", "Diagramm wurde geladen.")

    def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als Bild exportieren", "", "PNG-Bild (*.png);;JPEG-Bild (*.jpg)")
        if not path:
            return
        rect = self.scene.itemsBoundingRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        self.scene.render(painter, QRectF(image.rect()), rect)
        painter.end()
        image.save(path)
        QMessageBox.information(self, "Exportiert", "Bild wurde exportiert.")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als PDF exportieren", "", "PDF-Datei (*.pdf)")
        if not path:
            return
        from PyQt5.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        rect = self.scene.itemsBoundingRect()
        printer.setPaperSize(rect.size(), QPrinter.Point)
        painter = QPainter(printer)
        self.scene.render(painter, QRectF(printer.pageRect()), rect)
        painter.end()
        QMessageBox.information(self, "Exportiert", "PDF wurde exportiert.")

    def export_table(self):
        path, _ = QFileDialog.getSaveFileName(self, "Tabelle exportieren", "", "CSV-Datei (*.csv)")
        if not path:
            return
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        with open(path, 'w', encoding='utf-8') as f:
            for r in range(rows):
                line = []
                for c in range(cols):
                    item = self.table.item(r, c)
                    line.append(item.text() if item else "")
                f.write(','.join(line) + '\n')
        QMessageBox.information(self, "Exportiert", "Tabelle wurde exportiert.")

    def create_template(self):
        name, ok = QInputDialog.getText(self, "Template-Name", "Name des Templates:")
        if not ok or not name:
            return
        shapes = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
        shape_str, ok = QInputDialog.getItem(self, "Form wählen", "Form:", shapes, 0, False)
        if not ok:
            return
        mapping = {
            "Rechteck": "rect",
            "Ellipse": "ellipse",
            "Raute": "diamond",
            "Dreieck": "triangle",
            "Hexagon": "hexagon"
        }
        shape = mapping[shape_str]

        color = QColorDialog.getColor(QColor("lightgray"))
        color_name = color.name() if color.isValid() else "lightgray"

        width, ok = QInputDialog.getInt(self, "Breite eingeben", "Breite:", 100, 10, 1000, 1)
        if not ok:
            return
        height, ok = QInputDialog.getInt(self, "Höhe eingeben", "Höhe:", 60, 10, 1000, 1)
        if not ok:
            return
        text1, ok1 = QInputDialog.getText(self, "Text eingeben", "Textzeile 1:")
        if not ok1:
            return
        text2, ok2 = QInputDialog.getText(self, "Text eingeben", "Textzeile 2:")
        if not ok2:
            return

        tpl = Template(
            name=name,
            shape=shape,
            color=color_name,
            width=width,
            height=height,
            text1=text1,
            text2=text2
        )
        self.templates.append(tpl)
        item = self.create_template_item(tpl)
        self.template_list.addItem(item)
        self.save_templates()
        QMessageBox.information(self, "Template erstellt", f"Template '{name}' wurde erstellt.")

    def delete_template(self):
        current = self.template_list.currentItem()
        if not current:
            return
        row = self.template_list.row(current)
        del self.templates[row]
        self.template_list.takeItem(row)
        self.save_templates()

    def load_templates(self):
        if not os.path.exists(TEMPLATES_FILE):
            return
        with open(TEMPLATES_FILE, "r") as f:
            data = json.load(f)
        for tpl_data in data:
            tpl = Template(
                name=tpl_data.get("name", ""),
                shape=tpl_data.get("shape", "rect"),
                color=tpl_data.get("color", "lightgray"),
                width=tpl_data.get("width", 100),
                height=tpl_data.get("height", 60),
                text1=tpl_data.get("text1", ""),
                text2=tpl_data.get("text2", "")
            )
            self.templates.append(tpl)

    def save_templates(self):
        data = []
        for tpl in self.templates:
            data.append({
                "name": tpl.name,
                "shape": tpl.shape,
                "color": tpl.color,
                "width": tpl.width,
                "height": tpl.height,
                "text1": tpl.text1,
                "text2": tpl.text2
            })
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def update_table(self):
        # Tabelle neu erstellen: zuerst Knoten, dann Verbindungen
        total_rows = len(self.scene.nodes) + len(self.scene.edges)
        self.table.setRowCount(total_rows)
        row = 0
        # Knoten eintragen
        for node in self.scene.nodes:
            self.table.setItem(row, 0, QTableWidgetItem(node.text1))
            self.table.setItem(row, 1, QTableWidgetItem(node.text2))
            self.table.setItem(row, 2, QTableWidgetItem(node.shape))
            self.table.setItem(row, 3, QTableWidgetItem(node.brush.color().name()))
            row += 1
        # Verbindungen eintragen
        for edge in self.scene.edges:
            label = f"{self.scene.nodes.index(edge.source)} → {self.scene.nodes.index(edge.dest)}"
            self.table.setItem(row, 0, QTableWidgetItem("Verbindung"))
            self.table.setItem(row, 1, QTableWidgetItem(label))
            style_name = {
                Qt.SolidLine: "Durchgezogen",
                Qt.DashLine: "Gestrichelt",
                Qt.DotLine: "Gepunktet"
            }.get(edge.pen.style(), "Durchgezogen")
            self.table.setItem(row, 2, QTableWidgetItem(style_name))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            row += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
