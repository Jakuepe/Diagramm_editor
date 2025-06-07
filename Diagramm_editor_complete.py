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
    QPainterPath, QPolygonF
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QTransform
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

# ... (rest of the code continues similarly) ...
