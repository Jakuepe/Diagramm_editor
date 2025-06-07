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
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter, QImage, QPainterPath, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF, QTransform
from PyQt5.QtPrintSupport import QPrinter

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", text1="Node", text2="", color1=QColor("lightgray"), color2=QColor("white"), size=(100,60)):
        super().__init__(QRectF(0,0,*size))
        self.min_width, self.min_height = size
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.shape, self.color1, self.color2 = shape, color1, color2
        self.pen = QPen(Qt.black)
        self.setPen(self.pen)
        self.text1, self.text2 = text1, text2
        self.text_item1 = QGraphicsTextItem(text1, self)
        self.text_item1.setDefaultTextColor(Qt.black)
        f1=QFont(); f1.setPointSize(10)
        self.text_item1.setFont(f1)
        self.text_item2 = QGraphicsTextItem(text2, self)
        self.text_item2.setDefaultTextColor(Qt.black)
        f2=QFont(); f2.setPointSize(8)
        self.text_item2.setFont(f2)
        self.adjust_size(); self.center_texts()
    def adjust_size(self):
        pad=10
        b1=self.text_item1.boundingRect(); b2=self.text_item2.boundingRect()
        w=max(b1.width(),b2.width())+2*pad; h=b1.height()+b2.height()+2*pad
        self.setRect(0,0,max(w,self.min_width),max(h,self.min_height))
    def center_texts(self):
        r=self.rect(); b1=self.text_item1.boundingRect()
        self.text_item1.setPos((r.width()-b1.width())/2,5)
        b2=self.text_item2.boundingRect()
        self.text_item2.setPos((r.width()-b2.width())/2,5+b1.height())
    def paint(self,p,o,w):
        r=self.rect(); path=QPainterPath()
        if self.shape=="rect": path.addRect(r)
        elif self.shape=="ellipse": path.addEllipse(r)
        elif self.shape=="diamond":
            pts=[QPointF(r.x()+r.width()/2,r.y()),QPointF(r.x()+r.width(),r.y()+r.height()/2),QPointF(r.x()+r.width()/2,r.y()+r.height()),QPointF(r.x(),r.y()+r.height()/2)]
            path.addPolygon(QPolygonF(pts))
        elif self.shape=="triangle":
            pts=[QPointF(r.x()+r.width()/2,r.y()),QPointF(r.x()+r.width(),r.y()+r.height()),QPointF(r.x(),r.y()+r.height())]
            path.addPolygon(QPolygonF(pts))
        elif self.shape=="hexagon":
            w,h=r.width(),r.height(); x,y=r.x(),r.y();
            pts=[QPointF(x+w*0.25,y),QPointF(x+w*0.75,y),QPointF(x+w,y+h/2),QPointF(x+w*0.75,y+h),QPointF(x+w*0.25,y+h),QPointF(x,y+h/2)]
            path.addPolygon(QPolygonF(pts))
        painter=QPainter(w); painter.save(); painter.setBrush(QBrush(self.color1)); painter.setPen(self.pen)
        painter.setClipRect(QRectF(0,0,r.width(),r.height()/2)); painter.drawPath(path); painter.restore()
        painter.save(); painter.setBrush(QBrush(self.color2)); painter.setPen(self.pen)
        painter.setClipRect(QRectF(0,r.height()/2,r.width(),r.height()/2)); painter.drawPath(path); painter.restore()
        painter.setPen(self.pen); painter.drawPath(path); self.center_texts()
    def contextMenuEvent(self,e):
        menu=QMenu(); ac=[menu.addAction(t) for t in ["Farbe ändern","Form ändern","Verbinden","Text bearbeiten","Löschen"]]
        a=menu.exec_(e.screenPos()); s=self.scene()
        if a==ac[0]: c1=QColorDialog.getColor(self.color1);
            if c1.isValid(): c2=QColorDialog.getColor(self.color2); self.color1, self.color2=c1,(c2 if c2.isValid() else c1); self.update();s.parent.update_table()
        elif a==ac[1]: idx,ok=QInputDialog.getItem(None,"Form wählen","Form:",["Rechteck","Ellipse","Raute","Dreieck","Hexagon"],0,False);
            if ok: mp={'Rechteck':'rect','Ellipse':'ellipse','Raute':'diamond','Dreieck':'triangle','Hexagon':'hexagon'};self.shape=mp[idx];self.update();s.parent.update_table()
        elif a==ac[2]: s.connecting=True; s.connect_source=self
        elif a==ac[3]: t1,ok1=QInputDialog.getText(None,"Text1","Text:",text=self.text1);
            if ok1: t2,ok2=QInputDialog.getText(None,"Text2","Text:",text=self.text2);
            if ok2: self.text1,self.text2=t1,t2;self.text_item1.setPlainText(t1);self.text_item2.setPlainText(t2);self.adjust_size();self.center_texts();s.parent.update_table()
        elif a==ac[4]:
            for ed in list(s.edges):
                if ed.source==self or ed.dest==self: s.removeItem(ed); s.edges.remove(ed)
            s.removeItem(self); s.nodes.remove(self); s.parent.update_table()
        super().contextMenuEvent(e)

class EdgeItem(QGraphicsLineItem):
    def __init__(self,src,dest,style=Qt.SolidLine,label=""):
        super().__init__(); self.source, self.dest=src,dest; self.pen=QPen(Qt.black,2); self.pen.setStyle(style); self.setPen(self.pen)
        self.label=label; self.text_item=QGraphicsTextItem(label,self);f=QFont();f.setPointSize(8);self.text_item.setFont(f);self.text_item.setDefaultTextColor(Qt.black);self.update_position();self.setZValue(-1)
    def update_position(self):
        s=self.source.sceneBoundingRect().center();d=self.dest.sceneBoundingRect().center();self.setLine(s.x(),s.y(),d.x(),d.y());mx=(s.x()+d.x())/2;my=(s.y()+d.y())/2;r=self.text_item.boundingRect();self.text_item.setPos(mx-r.width()/2,my-r.height()-5)
    def paint(self,p,o,w): self.update_position(); painter=QPainter(w) if False else w; painter.setPen(self.pen); painter.drawLine(self.line())
    def contextMenuEvent(self,e):
        menu=QMenu(); c=menu.addAction("Farbe ändern");t=menu.addAction("Text bearbeiten");d=menu.addAction("Verbindung löschen");a=menu.exec_(e.screenPos());s=self.scene()
        if a==c: col=QColorDialog.getColor(self.pen.color());
            if col.isValid(): self.pen.setColor(col);self.setPen(self.pen);self.update();s.parent.update_table()
        elif a==t: txt,ok=QInputDialog.getText(None,"Verbindungstext","Text:",text=self.label);
            if ok: self.label=txt;self.text_item.setPlainText(txt);self.update_position();s.parent.update_table()
        elif a==d: s.removeItem(self);s.edges.remove(self);s.parent.update_table()
        super().contextMenuEvent(e)

class DiagramScene(QGraphicsScene):
    def __init__(self): super().__init__(); self.nodes=[];self.edges=[];self.connecting=False;self.connect_source=None;self.parent=None
    def mousePressEvent(self,e): item=self.itemAt(e.scenePos(),QTransform());
        if self.connecting and e.button()==Qt.LeftButton and isinstance(item,NodeItem):
            style,ok=QInputDialog.getItem(None,"Linienstil wählen","Stil:",["Durchgezogen","Gestrichelt","Gepunktet"],0,False);
            mapping={"Durchgezogen":Qt.SolidLine,"Gestrichelt":Qt.DashLine,"Gepunktet":Qt.DotLine};
            edge=EdgeItem(self.connect_source,item,mapping.get(style,Qt.SolidLine),"");self.addItem(edge);self.edges.append(edge);self.connecting=False;self.connect_source=None;self.parent.update_table()
        else: super().mousePressEvent(e)

class Template:
    def __init__(self,name,shape,color1,color2,width,height,text1,text2): self.name=name;self.shape=shape;self.color1=color1;self.color2=color2;self.width=width;self.height=height;self.text1=text1;self.text2=text2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Diagramm-Editor"); self.setGeometry(100,100,1000,600); self.scene=DiagramScene();self.scene.parent=self; self.view=QraphicsView(self.scene);self.setCentralWidget(self.view)
        self.templates=[];self.load_templates();self.init_ui();self.update_table()
    def init_ui(self): pass
    def add_node(self): pass
    # ... unfortunately truncated due to message size ...

if __name__ == "__main__":
    app=QApplication(sys.argv); w=MainWindow(); w.show(); sys.exit(app.exec_())
