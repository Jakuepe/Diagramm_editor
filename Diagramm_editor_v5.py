import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QFileDialog, QToolBar, QAction, QColorDialog,
    QInputDialog, QListWidget, QListWidgetItem, QDockWidget, QMessageBox, QMenu
)
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter, QImage, QTransform
from PyQt5.QtCore import Qt, QPointF, QRectF

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", rect=QRectF(0, 0, 100, 50), text="Node", color=QColor("lightgray")):
        super().__init__(rect)
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.shape = shape  # "rect" or "ellipse"
        self.brush = QBrush(color)
        self.pen = QPen(Qt.black)
        self.setBrush(self.brush)
        self.setPen(self.pen)
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)
        self.center_text()

    def center_text(self):
        rect = self.rect()
        text_rect = self.text_item.boundingRect()
        x = rect.x() + (rect.width() - text_rect.width()) / 2
        y = rect.y() + (rect.height() - text_rect.height()) / 2
        self.text_item.setPos(x, y)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        if self.shape == "rect":
            painter.drawRect(self.rect())
        elif self.shape == "ellipse":
            painter.drawEllipse(self.rect())
        self.center_text()

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        change_shape = menu.addAction("Form ändern")
        edit_text = menu.addAction("Text bearbeiten")
        delete_node = menu.addAction("Löschen")
        action = menu.exec_(event.screenPos())
        if action == change_color:
            color = QColorDialog.getColor(self.brush.color())
            if color.isValid():
                self.brush.setColor(color)
                self.update()
        elif action == change_shape:
            shapes = ["Rechteck", "Ellipse"]
            idx, ok = QInputDialog.getItem(None, "Form wählen", "Form:", shapes, 0, False)
            if ok:
                self.shape = "rect" if idx == "Rechteck" else "ellipse"
                self.update()
        elif action == edit_text:
            text, ok = QInputDialog.getText(None, "Text bearbeiten", "Neuer Text:", text=self.text_item.toPlainText())
            if ok:
                self.text_item.setPlainText(text)
                self.center_text()
        elif action == delete_node:
            for edge in list(self.scene().items()):
                if isinstance(edge, EdgeItem) and (edge.source == self or edge.dest == self):
                    self.scene().removeItem(edge)
            self.scene().removeItem(self)
        super().contextMenuEvent(event)

class EdgeItem(QGraphicsLineItem):
    def __init__(self, source: NodeItem, dest: NodeItem):
        super().__init__()
        self.source = source
        self.dest = dest
        self.pen = QPen(Qt.black, 2)
        self.setPen(self.pen)
        self.update_position()
        self.setZValue(-1)

    def update_position(self):
        src_center = self.source.sceneBoundingRect().center()
        dest_center = self.dest.sceneBoundingRect().center()
        self.setLine(src_center.x(), src_center.y(), dest_center.x(), dest_center.y())

    def paint(self, painter, option, widget):
        self.update_position()
        painter.setPen(self.pen)
        painter.drawLine(self.line())

class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.temp_edge = None
        self.connecting = False
        self.connect_source = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if self.connecting and isinstance(item, NodeItem):
            if self.connect_source is None:
                self.connect_source = item
            else:
                dest = item
                edge = EdgeItem(self.connect_source, dest)
                self.addItem(edge)
                self.edges.append(edge)
                self.connecting = False
                self.connect_source = None
        else:
            super().mousePressEvent(event)

class Template:
    def __init__(self, name, shape, color, width, height, text):
        self.name = name
        self.shape = shape
        self.color = color
        self.width = width
        self.height = height
        self.text = text

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramm-Editor")
        self.setGeometry(100, 100, 800, 600)

        self.scene = DiagramScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.templates = []
        self.load_templates()
        self.init_ui()

    def init_ui(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_node_action = QAction("Knoten hinzufügen", self)
        add_node_action.triggered.connect(self.add_node)
        toolbar.addAction(add_node_action)

        connect_action = QAction("Verbinden", self)
        connect_action.triggered.connect(self.start_connect)
        toolbar.addAction(connect_action)

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

        create_template_action = QAction("Template erstellen", self)
        create_template_action.triggered.connect(self.create_template)
        toolbar.addAction(create_template_action)

        # Template list dock
        self.template_list = QListWidget()
        for tpl in self.templates:
            item = QListWidgetItem(tpl.name)
            self.template_list.addItem(item)
        self.template_list.itemDoubleClicked.connect(self.add_node_from_template)
        dock = QDockWidget("Templates", self)
        dock.setWidget(self.template_list)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def add_node(self):
        # Default node
        node = NodeItem()
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
        self.scene.nodes.append(node)

    def add_node_from_template(self, item: QListWidgetItem):
        name = item.text()
        tpl = next((t for t in self.templates if t.name == name), None)
        if tpl:
            node = NodeItem(
                shape=tpl.shape,
                rect=QRectF(0, 0, tpl.width, tpl.height),
                text=tpl.text,
                color=QColor(tpl.color)
            )
            node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
            self.scene.addItem(node)
            self.scene.nodes.append(node)

    def start_connect(self):
        self.scene.connecting = True
        self.scene.connect_source = None
        QMessageBox.information(self, "Verbinden", "Klicken Sie auf zwei Knoten, um sie zu verbinden.")

    def save_diagram(self):
        path, _ = QFileDialog.getSaveFileName(self, "Diagramm speichern", "", "JSON-Datei (*.json)")
        if not path:
            return
        data = {
            "nodes": [],
            "edges": []
        }
        for idx, node in enumerate(self.scene.nodes):
            data["nodes"].append({
                "id": idx,
                "shape": node.shape,
                "color": node.brush.color().name(),
                "x": node.pos().x(),
                "y": node.pos().y(),
                "width": node.rect().width(),
                "height": node.rect().height(),
                "text": node.text_item.toPlainText()
            })
        for edge in self.scene.edges:
            src_id = self.scene.nodes.index(edge.source)
            dest_id = self.scene.nodes.index(edge.dest)
            data["edges"].append({"source": src_id, "dest": dest_id})
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Gespeichert", "Diagramm wurde gespeichert.")

    def load_diagram(self):
        path, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "JSON-Datei (*.json)")
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)
        # Clear scene
        for item in self.scene.items():
            self.scene.removeItem(item)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        # Create nodes
        for node_data in data.get("nodes", []):
            node = NodeItem(
                shape=node_data.get("shape", "rect"),
                rect=QRectF(0, 0, node_data.get("width", 100), node_data.get("height", 50)),
                text=node_data.get("text", "Node"),
                color=QColor(node_data.get("color", "lightgray"))
            )
            node.setPos(node_data.get("x", 0), node_data.get("y", 0))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
        # Create edges
        for edge_data in data.get("edges", []):
            src = self.scene.nodes[edge_data.get("source")]
            dest = self.scene.nodes[edge_data.get("dest")]
            edge = EdgeItem(src, dest)
            self.scene.addItem(edge)
            self.scene.edges.append(edge)
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

    def create_template(self):
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], NodeItem):
            QMessageBox.warning(self, "Kein Knoten ausgewählt", "Bitte wählen Sie einen Knoten aus, um ein Template zu erstellen.")
            return
        node = selected[0]
        name, ok = QInputDialog.getText(self, "Template-Name", "Name des Templates:")
        if not ok or not name:
            return
        tpl = Template(
            name=name,
            shape=node.shape,
            color=node.brush.color().name(),
            width=int(node.rect().width()),
            height=int(node.rect().height()),
            text=node.text_item.toPlainText()
        )
        self.templates.append(tpl)
        self.template_list.addItem(tpl.name)
        self.save_templates()
        QMessageBox.information(self, "Template erstellt", f"Template '{name}' wurde erstellt.")

    def load_templates(self):
        if not os.path.exists(TEMPLATES_FILE):
            return
        with open(TEMPLATES_FILE, "r") as f:
            data = json.load(f)
        for tpl_data in data:
            tpl = Template(
                name=tpl_data.get("name"),
                shape=tpl_data.get("shape", "rect"),
                color=tpl_data.get("color", "lightgray"),
                width=tpl_data.get("width", 100),
                height=tpl_data.get("height", 50),
                text=tpl_data.get("text", "Node")
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
                "text": tpl.text
            })
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
