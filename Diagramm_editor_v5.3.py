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
    QBrush, QColor, QPen, QFont, QPainter, QImage,
    QPainterPath, QPolygonF, QTransform
)
from PyQt5.QtCore import Qt, QPointF, QRectF
# QTransform moved to QtGui for PyQt5 compatibility
from PyQt5.QtGui import QTransform
from PyQt5.QtPrintSupport import QPrinter

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", text1="Node", text2="", color1=QColor("lightgray"), color2=QColor("white"), size=(100, 60)):
        super().__init__(QRectF(0, 0, *size))
        self.min_width, self.min_height = size
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
        font1 = QFont(); font1.setPointSize(10)
        self.text_item1.setFont(font1)
        self.text_item2 = QGraphicsTextItem(text2, self)
        self.text_item2.setDefaultTextColor(Qt.black)
        font2 = QFont(); font2.setPointSize(8)
        self.text_item2.setFont(font2)

        self.adjust_size()
        self.center_texts()

    def adjust_size(self):
        padding = 10
        r1 = self.text_item1.boundingRect()
        r2 = self.text_item2.boundingRect()
        w = max(r1.width(), r2.width()) + padding * 2
        h = r1.height() + r2.height() + padding * 2
        self.setRect(0, 0, max(w, self.min_width), max(h, self.min_height))

    def center_texts(self):
        r = self.rect()
        b1 = self.text_item1.boundingRect()
        self.text_item1.setPos((r.width() - b1.width()) / 2, 5)
        b2 = self.text_item2.boundingRect()
        self.text_item2.setPos((r.width() - b2.width()) / 2, 5 + b1.height())

    def paint(self, painter, option, widget):
        r = self.rect()
        path = QPainterPath()
        if self.shape == "rect":
            path.addRect(r)
        elif self.shape == "ellipse":
            path.addEllipse(r)
        elif self.shape == "diamond":
            pts = [
                QPointF(r.x()+r.width()/2, r.y()), QPointF(r.x()+r.width(), r.y()+r.height()/2),
                QPointF(r.x()+r.width()/2, r.y()+r.height()), QPointF(r.x(), r.y()+r.height()/2)
            ]
            path.addPolygon(QPolygonF(pts))
        elif self.shape == "triangle":
            pts = [
                QPointF(r.x()+r.width()/2, r.y()), QPointF(r.x()+r.width(), r.y()+r.height()),
                QPointF(r.x(), r.y()+r.height())
            ]
            path.addPolygon(QPolygonF(pts))
        elif self.shape == "hexagon":
            w, h = r.width(), r.height()
            x, y = r.x(), r.y()
            pts = [
                QPointF(x+w*0.25, y), QPointF(x+w*0.75, y), QPointF(x+w, y+h/2),
                QPointF(x+w*0.75, y+h), QPointF(x+w*0.25, y+h), QPointF(x, y+h/2)
            ]
            path.addPolygon(QPolygonF(pts))
        # Fill top half
        painter.save()
        painter.setBrush(QBrush(self.color1))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(0, 0, r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Fill bottom half
        painter.save()
        painter.setBrush(QBrush(self.color2))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(0, r.height()/2, r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Outline
        painter.setPen(self.pen)
        painter.drawPath(path)
        self.center_texts()

    def contextMenuEvent(self, event):
        menu = QMenu()
        color_act = menu.addAction("Farbe ändern")
        shape_act = menu.addAction("Form ändern")
        conn_act = menu.addAction("Verbinden")
        text_act = menu.addAction("Text bearbeiten")
        del_act = menu.addAction("Löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == color_act:
            c1 = QColorDialog.getColor(self.color1)
            if c1.isValid():
                c2 = QColorDialog.getColor(self.color2)
                self.color1, self.color2 = c1, (c2 if c2.isValid() else c1)
                self.update()
                scene.parent.update_table()
        elif action == shape_act:
            shapes = ["Rechteck","Ellipse","Raute","Dreieck","Hexagon"]
            idx, ok = QInputDialog.getItem(None, "Form wählen", "Form:", shapes, 0, False)
            if ok:
                mapping = {'Rechteck':'rect','Ellipse':'ellipse','Raute':'diamond','Dreieck':'triangle','Hexagon':'hexagon'}
                self.shape = mapping[idx]
                self.update()
                scene.parent.update_table()
        elif action == conn_act:
            scene.connecting = True
            scene.connect_source = self
        elif action == text_act:
            t1, ok1 = QInputDialog.getText(None, "Textzeile 1", "Text:", text=self.text1)
            if ok1:
                t2, ok2 = QInputDialog.getText(None, "Textzeile 2", "Text:", text=self.text2)
                if ok2:
                    self.text1, self.text2 = t1, t2
                    self.text_item1.setPlainText(t1)
                    self.text_item2.setPlainText(t2)
                    self.adjust_size()
                    self.center_texts()
                    scene.parent.update_table()
        elif action == del_act:
            for e in list(scene.edges):
                if e.source == self or e.dest == self:
                    scene.removeItem(e)
                    scene.edges.remove(e)
            scene.removeItem(self)
            scene.nodes.remove(self)
            scene.parent.update_table()
        super().contextMenuEvent(event)

class EdgeItem(QGraphicsLineItem):
    def __init__(self, source, dest, style=Qt.SolidLine, label=""):
        super().__init__()
        self.source = source
        self.dest = dest
        self.pen = QPen(Qt.black, 2)
        self.pen.setStyle(style)
        self.setPen(self.pen)
        self.label = label
        self.text_item = QGraphicsTextItem(label, self)
        f = QFont(); f.setPointSize(8)
        self.text_item.setFont(f)
        self.text_item.setDefaultTextColor(Qt.black)
        self.update_position()
        self.setZValue(-1)

    def update_position(self):
        s = self.source.sceneBoundingRect().center()
        d = self.dest.sceneBoundingRect().center()
        self.setLine(s.x(), s.y(), d.x(), d.y())
        mx = (s.x() + d.x()) / 2
        my = (s.y() + d.y()) / 2
        r = self.text_item.boundingRect()
        self.text_item.setPos(mx - r.width()/2, my - r.height() - 5)

    def paint(self, painter, option, widget):
        self.update_position()
        painter.setPen(self.pen)
        painter.drawLine(self.line())

    def contextMenuEvent(self, event):
        menu = QMenu()
        color_act = menu.addAction("Farbe ändern")
        text_act = menu.addAction("Text bearbeiten")
        del_act = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == color_act:
            c = QColorDialog.getColor(self.pen.color())
            if c.isValid():
                self.pen.setColor(c)
                self.setPen(self.pen)
                self.update()
                scene.parent.update_table()
        elif action == text_act:
            t, ok = QInputDialog.getText(None, "Verbindungstext", "Text:", text=self.label)
            if ok:
                self.label = t
                self.text_item.setPlainText(t)
                self.update_position()
                scene.parent.update_table()
        elif action == del_act:
            scene.removeItem(self)
            scene.edges.remove(self)
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
            styles = ["Durchgezogen", "Gestrichelt", "Gepunktet"]
            choice, ok = QInputDialog.getItem(None, "Linienstil wählen", "Stil:", styles, 0, False)
            mapping = {"Durchgezogen": Qt.SolidLine, "Gestrichelt": Qt.DashLine, "Gepunktet": Qt.DotLine}
            style = mapping.get(choice, Qt.SolidLine)
            edge = EdgeItem(self.connect_source, item, style, "")
            self.addItem(edge)
            self.edges.append(edge)
            self.connecting = False
            self.connect_source = None
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

        actions = [
            ("Knoten hinzufügen", self.add_node),
            ("Neue Seite", self.new_page),
            ("Speichern", self.save_diagram),
            ("Laden", self.load_diagram),
            ("Als Bild exportieren", self.export_image),
            ("Als PDF exportieren", self.export_pdf),
            ("Tabelle exportieren", self.export_table),
            ("Template erstellen", self.create_template),
            ("Template löschen", self.delete_template),
        ]
        for text, fn in actions:
            act = QAction(text, self)
            act.triggered.connect(fn)
            toolbar.addAction(act)
        # Templates Dock
        self.template_list = QListWidget()
        self.template_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_list.customContextMenuRequested.connect(self.show_template_context_menu)
        for tpl in self.templates:
            self.template_list.addItem(QListWidgetItem(tpl.name))
        self.template_list.itemDoubleClicked.connect(self.add_node_from_template)
        temp_dock = QDockWidget("Templates", self)
        temp_dock.setWidget(self.template_list)
        self.addDockWidget(Qt.RightDockWidgetArea, temp_dock)
        # Table Dock
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Text1", "Text2", "Form", "Farbe1/Farbe2"])
        table_dock = QDockWidget("Tabelle", self)
        table_dock.setWidget(self.table)
        self.addDockWidget(Qt.RightDockWidgetArea, table_dock)

    def add_node(self):
        node = NodeItem()
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
        self.scene.nodes.append(node)
        self.update_table()

    def add_node_from_template(self, item: QListWidgetItem):
        tpl = next((t for t in self.templates if t.name == item.text()), None)
        if tpl:
            node = NodeItem(
                shape=tpl.shape,
                text1=tpl.text1,
                text2=tpl.text2,
                color1=QColor(tpl.color1),
                color2=QColor(tpl.color2),
                size=(tpl.width, tpl.height)
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
            src = self.scene.nodes.index(edge.source)
            dest = self.scene.nodes.index(edge.dest)
            data["edges"].append({
                "source": src,
                "dest": dest,
                "style": edge.pen.style(),
                "label": edge.label
            })
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Gespeichert", "Diagramm wurde gespeichert.")

        def load_diagram(self):
        path, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "JSON-Datei (*.json)")
        if not path:
            return
        with open(path) as f:
            data = json.load(f)
        self.new_page()
        for nd in data.get("nodes", []):
            node = NodeItem(
                shape=nd.get("shape", "rect"),
                text1=nd.get("text1", ""),
                text2=nd.get("text2", ""),
                color1=QColor(nd.get("color1", "lightgray")),
                color2=QColor(nd.get("color2", "white")),
                size=(nd.get("width", 100), nd.get("height", 60))
            )
            node.setPos(nd.get("x", 0), nd.get("y", 0))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
        for ed in data.get("edges", []):
            src = self.scene.nodes[ed.get("source")]
            dest = self.scene.nodes[ed.get("dest")]
            edge = EdgeItem(src, dest, ed.get("style", Qt.SolidLine), ed.get("label", ""))
            self.scene.addItem(edge)
            self.scene.edges.append(edge)
        self.update_table()
        QMessageBox.information(self, "Geladen", "Diagramm wurde geladen.")

        def export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als Bild exportieren", "", "PNG (*.png);;JPEG (*.jpg)")
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
        path, _ = QFileDialog.getSaveFileName(self, "Als PDF exportieren", "", "PDF (*.pdf)")
        if not path:
            return
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
                line = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(cols)]
                f.write(','.join(line) + '
')
        QMessageBox.information(self, "Exportiert", "Tabelle wurde exportiert.")

        def create_template(self):
        name, ok = QInputDialog.getText(self, "Template-Name", "Name des Templates:")
        if not ok or not name:
            return
        shapes = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
        shape_str, ok = QInputDialog.getItem(self, "Form wählen", "Form:", shapes, 0, False)
        if not ok:
            return
        mapping = {"Rechteck": "rect", "Ellipse": "ellipse", "Raute": "diamond", "Dreieck": "triangle", "Hexagon": "hexagon"}
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
        text1, ok1 = QInputDialog.getText(self, "Textzeile 1", "Text:")
        if not ok1:
            return
        text2, ok2 = QInputDialog.getText(self, "Textzeile 2", "Text:")
        if not ok2:
            return
        tpl = Template(name, mapping[shape_str], color1, color2, width, height, text1, text2)
        self.templates.append(tpl)
        self.template_list.addItem(QListWidgetItem(tpl.name))
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

        def load_templates(self):
        if not os.path.exists(TEMPLATES_FILE):
            return
        with open(TEMPLATES_FILE, "r") as f:
            data = json.load(f)
        for td in data:
            tpl = Template(
                td.get("name", ""),
                td.get("shape", "rect"),
                td.get("color1", "lightgray"),
                td.get("color2", "white"),
                td.get("width", 100),
                td.get("height", 60),
                td.get("text1", ""),
                td.get("text2", "")
            )
            self.templates.append(tpl)

        def save_templates(self):
        data = []
        for t in self.templates:
            data.append({
                "name": t.name,
                "shape": t.shape,
                "color1": t.color1,
                "color2": t.color2,
                "width": t.width,
                "height": t.height,
                "text1": t.text1,
                "text2": t.text2
            })
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(data, f, indent=4)

        def update_table(self):
        total = len(self.scene.nodes) + len(self.scene.edges)
        self.table.setRowCount(total)
        r = 0
        # Nodes
        for n in self.scene.nodes:
            self.table.setItem(r, 0, QTableWidgetItem(n.text1))
            self.table.setItem(r, 1, QTableWidgetItem(n.text2))
            self.table.setItem(r, 2, QTableWidgetItem(n.shape))
            self.table.setItem(r, 3, QTableWidgetItem(f"{n.color1.name()}/{n.color2.name()}"))
            r += 1
        # Edges
        for e in self.scene.edges:
            s = e.source.text1
            d = e.dest.text1
            self.table.setItem(r, 0, QTableWidgetItem("Verbindung"))
            self.table.setItem(r, 1, QTableWidgetItem(f"{s} → {d}"))
            style_name = {Qt.SolidLine: "Durchgezogen", Qt.DashLine: "Gestrichelt", Qt.DotLine: "Gepunktet"}.get(e.pen.style(), "Durchgezogen")
            self.table.setItem(r, 2, QTableWidgetItem(style_name))
            self.table.setItem(r, 3, QTableWidgetItem(e.label))
            r += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
