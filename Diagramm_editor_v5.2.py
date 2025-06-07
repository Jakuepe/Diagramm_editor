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
    QPolygonF, QPixmap, QIcon, QPainterPath
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QPoint

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", rect=QRectF(0, 0, 100, 60), text1="Node", text2="", color1=QColor("lightgray"), color2=QColor("white")):
        super().__init__(rect)
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.shape = shape
        self.color1 = color1
        self.color2 = color2
        self.pen = QPen(Qt.black)
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
        text1_rect = self.text_item1.boundingRect()
        x1 = rect.x() + (rect.width() - text1_rect.width()) / 2
        y1 = rect.y() + 5
        self.text_item1.setPos(x1, y1)
        text2_rect = self.text_item2.boundingRect()
        x2 = rect.x() + (rect.width() - text2_rect.width()) / 2
        y2 = y1 + text1_rect.height()
        self.text_item2.setPos(x2, y2)

    def paint(self, painter, option, widget):
        r = self.rect()
        path = QPainterPath()
        if self.shape == "rect":
            path.addRect(r)
        elif self.shape == "ellipse":
            path.addEllipse(r)
        elif self.shape == "diamond":
            points = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height()/2),
                QPointF(r.x() + r.width()/2, r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height()/2)
            ]
            path.addPolygon(QPolygonF(points))
        elif self.shape == "triangle":
            points = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height())
            ]
            path.addPolygon(QPolygonF(points))
        elif self.shape == "hexagon":
            w, h = r.width(), r.height()
            x, y = r.x(), r.y()
            points = [
                QPointF(x + w*0.25, y),
                QPointF(x + w*0.75, y),
                QPointF(x + w, y + h/2),
                QPointF(x + w*0.75, y + h),
                QPointF(x + w*0.25, y + h),
                QPointF(x, y + h/2)
            ]
            path.addPolygon(QPolygonF(points))
        # Top half
        painter.save()
        painter.setBrush(QBrush(self.color1))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y(), r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Bottom half
        painter.save()
        painter.setBrush(QBrush(self.color2))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y() + r.height()/2, r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Outline
        painter.setPen(self.pen)
        painter.drawPath(path)
        self.center_texts()

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        change_shape = menu.addAction("Form ändern")
        connect_node = menu.addAction("Verbinden")
        edit_text = menu.addAction("Text bearbeiten")
        delete_node = menu.addAction("Löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == change_color and scene:
            col1 = QColorDialog.getColor(self.color1)
            if col1.isValid():
                col2 = QColorDialog.getColor(self.color2)
                if not col2.isValid():
                    col2 = col1
                self.color1 = col1
                self.color2 = col2
                self.update()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == change_shape and scene:
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
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == connect_node and scene:
            scene.connecting = True
            scene.connect_source = self
        elif action == edit_text and scene:
            text1, ok1 = QInputDialog.getText(None, "Primärer Text", "Textzeile 1:", text=self.text1)
            if ok1:
                text2, ok2 = QInputDialog.getText(None, "Sekundärer Text", "Textzeile 2:", text=self.text2)
                if ok2:
                    self.text1 = text1
                    self.text2 = text2
                    self.text_item1.setPlainText(text1)
                    self.text_item2.setPlainText(text2)
                    self.center_texts()
                    if hasattr(scene, 'parent'):
                        scene.parent.update_table()
        elif action == delete_node and scene:
            for edge in list(scene.items()):
                if isinstance(edge, EdgeItem) and (edge.source == self or edge.dest == self):
                    scene.removeItem(edge)
                    if edge in scene.edges:
                        scene.edges.remove(edge)
            scene.removeItem(self)
            if self in scene.nodes:
                scene.nodes.remove(self)
            if hasattr(scene, 'parent'):
                scene.parent.update_table()
        super().contextMenuEvent(event)

class EdgeItem(QGraphicsLineItem):
    def __init__(self, source: NodeItem, dest: NodeItem, line_style=Qt.SolidLine, label_text=""):
        super().__init__()
        self.source = source
        self.dest = dest
        self.pen = QPen(Qt.black, 2)
        self.pen.setStyle(line_style)
        self.setPen(self.pen)
        self.label_text = label_text
        self.text_item = QGraphicsTextItem(label_text, self)
        self.text_item.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(8)
        self.text_item.setFont(font)
        self.update_position()
        self.setZValue(-1)

    def update_position(self):
        src_c = self.source.sceneBoundingRect().center()
        dest_c = self.dest.sceneBoundingRect().center()
        self.setLine(src_c.x(), src_c.y(), dest_c.x(), dest_c.y())
        # Positioniere Label in der Mitte der Linie
        mx = (src_c.x() + dest_c.x()) / 2
        my = (src_c.y() + dest_c.y()) / 2
        self.text_item.setPos(mx - self.text_item.boundingRect().width()/2,
                              my - self.text_item.boundingRect().height()/2)

    def paint(self, painter, option, widget):
        self.update_position()
        painter.setPen(self.pen)
        painter.drawLine(self.line())

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_label = menu.addAction("Text bearbeiten")
        delete_edge = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == edit_label and scene:
            text, ok = QInputDialog.getText(None, "Verbindungstext", "Text für Verbindung:", text=self.label_text)
            if ok:
                self.label_text = text
                self.text_item.setPlainText(text)
                self.update_position()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == delete_edge and scene:
            scene.removeItem(self)
            if self in scene.edges:
                scene.edges.remove(self)
            if hasattr(scene, 'parent'):
                scene.parent.update_table()
        super().contextMenuEvent(event)

class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.connecting = False
        self.connect_source = None
        self.parent = None

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
            if self.parent:
                self.parent.update_table()
        else:
            super().mousePressEvent(event)

class Template:
    def __init__(self, name, shape, color1, color2, width, height, text1, text2):
        self.name = name
        self.shape = shape
        self.color1 = color1
        self.color2 = color2
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
        self.table.setHorizontalHeaderLabels(["Text1", "Text2", "Form/Verbindung", "Farbe1/Farbe2"])
        table_dock = QDockWidget("Tabelle", self)
        table_dock.setWidget(self.table)
        self.addDockWidget(Qt.RightDockWidgetArea, table_dock)

    def create_template_item(self, tpl):
        item = QListWidgetItem(tpl.name)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        # Zweifarbiges Icon
        r = QRectF(0, 0, 32, 32)
        path = QPainterPath()
        if tpl.shape == "rect":
            path.addRect(r)
        elif tpl.shape == "ellipse":
            path.addEllipse(r)
        elif tpl.shape == "diamond":
            points = [QPointF(16, 0), QPointF(32, 16), QPointF(16, 32), QPointF(0, 16)]
            path.addPolygon(QPolygonF(points))
        elif tpl.shape == "triangle":
            points = [QPointF(16, 0), QPointF(32, 32), QPointF(0, 32)]
            path.addPolygon(QPolygonF(points))
        elif tpl.shape == "hexagon":
            pts = [
                QPointF(8, 0), QPointF(24, 0), QPointF(32, 16),
                QPointF(24, 32), QPointF(8, 32), QPointF(0, 16)
            ]
            path.addPolygon(QPolygonF(pts))
        painter.save()
        painter.setBrush(QBrush(QColor(tpl.color1)))
        painter.setPen(QPen(Qt.black))
        painter.setClipRect(QRectF(0, 0, 32, 16))
        painter.drawPath(path)
        painter.restore()
        painter.save()
        painter.setBrush(QBrush(QColor(tpl.color2)))
        painter.setPen(QPen(Qt.black))
        painter.setClipRect(QRectF(0, 16, 32, 16))
        painter.drawPath(path)
        painter.restore()
        painter.setPen(QPen(Qt.black))
        painter.drawPath(path)
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
                color1=QColor(tpl.color1),
                color2=QColor(tpl.color2)
            )
            node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
            self.update_table()

    def new_page(self):
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
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
                "color1": node.color1.name(),
                "color2": node.color2.name(),
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
            label = edge.label_text
            data["edges"].append({"source": src_id, "dest": dest_id, "style": style, "label": label})
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Gespeichert", "Diagramm wurde gespeichert.")

    def load_diagram(self):
        path, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "JSON-Datei (*.json)")
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        for node_data in data.get("nodes", []):
            node = NodeItem(
                shape=node_data.get("shape", "rect"),
                rect=QRectF(0, 0, node_data.get("width", 100), node_data.get("height", 60)),
                text1=node_data.get("text1", ""),
                text2=node_data.get("text2", ""),
                color1=QColor(node_data.get("color1", "lightgray")),
                color2=QColor(node_data.get("color2", "white"))
            )
            node.setPos(node_data.get("x", 0), node_data.get("y", 0))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
        for edge_data in data.get("edges", []):
            src = self.scene.nodes[edge_data.get("source")]
            dest = self.scene.nodes[edge_data.get("dest")]
            style = edge_data.get("style", Qt.SolidLine)
            label = edge_data.get("label", "")
            edge = EdgeItem(src, dest, style, label)
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

        col1 = QColorDialog.getColor(QColor("lightgray"))
        color1 = col1.name() if col1.isValid() else "lightgray"
        col2 = QColorDialog.getColor(QColor("white"))
        color2 = col2.name() if col2.isValid() else "white"

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
            color1=color1,
            color2=color2,
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
                color1=tpl_data.get("color1", "lightgray"),
                color2=tpl_data.get("color2", "white"),
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
                "color1": tpl.color1,
                "color2": tpl.color2,
                "width": tpl.width,
                "height": tpl.height,
                "text1": tpl.text1,
                "text2": tpl.text2
            })
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def update_table(self):
        total_rows = len(self.scene.nodes) + len(self.scene.edges)
        self.table.setRowCount(total_rows)
        row = 0
        # Knoten
        for node in self.scene.nodes:
            self.table.setItem(row, 0, QTableWidgetItem(node.text1))
            self.table.setItem(row, 1, QTableWidgetItem(node.text2))
            self.table.setItem(row, 2, QTableWidgetItem(node.shape))
            self.table.setItem(row, 3, QTableWidgetItem(f"{node.color1.name()}/{node.color2.name()}"))
            row += 1
        # Verbindungen
        for edge in self.scene.edges:
            src_label = edge.source.text1
            dest_label = edge.dest.text1
            self.table.setItem(row, 0, QTableWidgetItem("Verbindung"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{src_label} → {dest_label}"))
            style_name = {
                Qt.SolidLine: "Durchgezogen",
                Qt.DashLine: "Gestrichelt",
                Qt.DotLine: "Gepunktet"
            }.get(edge.pen.style(), "Durchgezogen")
            self.table.setItem(row, 2, QTableWidgetItem(style_name))
            self.table.setItem(row, 3, QTableWidgetItem(edge.label_text))
            row += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
