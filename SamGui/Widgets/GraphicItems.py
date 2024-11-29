import uuid
from PIL import Image
from uuid import UUID
from typing import Optional
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from SamGui.Controller import CanvasController
from SamGui.Data import Edge, Label, BBoxPosition, AnchorPosition
from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath, QPixmap, QPainter
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsPixmapItem


class AnnotationItem:
    def __init__(self):
        super(AnnotationItem, self).__init__()
        self.guid = uuid.uuid1()
        self.label = "Annotation"

    def set_name(self, name: str):
        self.label = name

    def set_guid(self, guid: UUID):
        self.guid = guid


class PixmapImage(QGraphicsPixmapItem):
    def __init__(self, guid: UUID, image_path: str, controller: CanvasController):
        super().__init__()
        self.guid = guid
        self.image_path = image_path
        self.current_position = self.scenePos()
        self.pixmap = QPixmap(self.image_path)
        self.setPixmap(self.pixmap)
        self.controller = controller
        #self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    def update_position(self, x: int, y: int):
        self.setPos(x, y)
        self.current_position = self.scenePos()


class MaskPreview(AnnotationItem, QGraphicsPixmapItem):
    def __init__(self, guid: UUID, image: Image, pixmap: QPixmap, controller: CanvasController, parent: Optional[QGraphicsItem] = None):
        super().__init__()
        self.parent = parent
        self.setParentItem(self.parent)
        self.image = image  # keep an instance of the original for export
        self.setPixmap(pixmap)
        self.guid = guid
        self.current_position = self.scenePos()
        self.controller = controller

    def update_position(self, x: int, y: int):
        self.setPos(x, y)
        self.current_position = self.scenePos()


class AnchorPoint(AnnotationItem, QGraphicsEllipseItem):
    def __init__(
        self,
        guid: UUID,
        controller: CanvasController,
        x_pos: int = 0,
        y_pos: int = 0,
        width: int = 10,
        height: int = 10,
        label: str = "Anchor",
        class_id: Label = Label.foreground,
        parent: Optional[QGraphicsItem] = None
    ):
        super(AnchorPoint, self).__init__()
        self.guid = guid
        self.controller = controller
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.label = label
        self.class_id = class_id
        self.parent_item = parent
        self.setParentItem(self.parent_item)
        self.setPos(self.x_pos, self.y_pos)
        self.current_position = self.scenePos()
        self.setRect(0, 0, width, height)
        self.default_brush = (
            QBrush(Qt.GlobalColor.green)
            if self.class_id == Label.foreground
            else QBrush(Qt.GlobalColor.darkMagenta)
        )
        self.highlight_brush = QBrush(Qt.GlobalColor.yellow)
        self.setBrush(self.default_brush)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def highlight_on(self):
        self.setBrush(self.highlight_brush)
        self.update()

    def highlight_off(self):
        self.setBrush(self.default_brush)
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.current_position = value
            position = AnchorPosition(self.guid, self.x_pos, self.y_pos)
            self.controller.s_update_anchor_position.emit(position)
        else:
            return value

    def set_class(self, class_id: Label):
        if class_id == Label.foreground:
            self.default_brush = QBrush(Qt.GlobalColor.green)
            self.setBrush(self.default_brush)
        else:
            self.default_brush = QBrush(Qt.GlobalColor.darkMagenta)
            self.setBrush(self.default_brush)

        self.class_id = class_id


class BBoxRect(AnnotationItem, QGraphicsItem):
    s_update_pos = Signal(QPointF)

    def __init__(
        self, guid: UUID, controller: CanvasController, start_point: QPointF, end_point: QPointF, parent: Optional[QGraphicsItem] = None
    ):
        super().__init__()
        self.guid = guid
        self.controller = controller
        self.parent = parent
        self.setParentItem(self.parent)
        self.start_point = start_point
        self.end_point = end_point
        self.width = end_point.x() - start_point.x()
        self.height = end_point.y() - start_point.y()
        self.is_selected = False
        self.current_position = QPointF(self.start_point.x(), self.start_point.y())
        self.setPos(self.start_point)

        self.edge_size = 10
        self.clicked_pos = None
        self.original_rect = None
        self.selected_edge = None
        self.is_hovered = False
        self.edge_hovering = False
        self.is_resized = False

        self._pen_default = QPen(QColor(Qt.GlobalColor.red))
        self._pen_hover = QPen(QColor("#00ffdd"))
        self._pen_selected = QPen(QColor("#FFFFA637"))

        self.current_pen = self._pen_default

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)
            
    def update_stats(self, start_point: QPointF, end_point: QPointF):
        self.start_point = start_point
        self.end_point = end_point
        self.width = end_point.x() - start_point.x()
        self.height = end_point.y() - start_point.y()
        self.current_position = QPointF(self.start_point.x(), self.start_point.y())
        self.setPos(self.start_point)
        position = BBoxPosition(self.guid, start_point.x(), start_point.y(), self.width, self.height)
        self.controller.s_update_bbox_position.emit(position)

    def check_for_edge(self, event):
        self.clicked_pos = event.pos()

        rect = self.boundingRect()
        self.original_rect = rect
        _is_over_edge = False

        if abs(rect.left() - self.clicked_pos.x()) < self.edge_size:
            self.is_resized = True  # set this flag to True block eventual position updates by the GraphicsScene
            self.edge_hovering = True
            self.selected_edge = Edge.Left

            return True

        elif abs(rect.right() - self.clicked_pos.x()) < self.edge_size:
            self.is_resized = True  # set this flag to True block eventual position updates by the GraphicsScene
            self.edge_hovering = True
            self.selected_edge = Edge.Right

            return True

        elif abs(rect.bottom() - self.clicked_pos.y()) < self.edge_size:
            self.is_resized = True
            self.edge_hovering = True
            self.selected_edge = Edge.Bottom

            return True

        elif abs(rect.top() - self.clicked_pos.y()) < self.edge_size:
            self.is_resized = True
            self.edge_hovering = True
            self.selected_edge = Edge.Top

            return True

        else:
            self.is_resized = False
            self.edge_hovering = False
            self.selected_edge = None
            return False


    def mousePressEvent(self, event):
        self.check_for_edge(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        _event_pos = event.pos()

        if self.selected_edge is None:
            super().mouseMoveEvent(event)

        else:
            new_start = self.start_point
            new_end = self.end_point

            if self.selected_edge == Edge.Left:
                x_diff = _event_pos.x() - self.clicked_pos.x()
                new_x = self.start_point.x() + x_diff

                if new_x <= self.end_point.x() - self.edge_size-1:
                    new_start = QPointF(new_x, self.start_point.y())
                else:
                    new_x = self.end_point.x() - self.edge_size-1
                    new_start = QPointF(new_x, self.start_point.y())


            elif self.selected_edge == Edge.Right:

                scene_event_pos = self.mapToScene(_event_pos.x(), _event_pos.y())
                new_x = scene_event_pos.x()

                if new_x >= self.start_point.x() + self.edge_size + 1:
                    new_end = QPointF(new_x, self.end_point.y())
                else:
                    new_end = QPointF(self.start_point.x() + self.edge_size + 1, self.end_point.y())

            elif self.selected_edge == Edge.Top:
                y_diff = _event_pos.y() - self.clicked_pos.y()
                new_y =  self.start_point.y() + y_diff

                if new_y <= self.end_point.y() - self.edge_size - 1:
                    new_start = QPointF(self.start_point.x(), new_y)
                else:
                    new_start = QPointF(self.start_point.x(), self.start_point.y() - self.edge_size - 1)

            elif self.selected_edge == Edge.Bottom:
                scene_event_pos = self.mapToScene(_event_pos.x(), _event_pos.y())
                new_y = scene_event_pos.y()

                if new_y >= self.start_point.y() + self.edge_size + 1:
                    new_end = QPointF(self.end_point.x(), new_y)
                else:
                    new_end = QPointF(self.end_point.x(), self.start_point.y() + self.edge_size + 1)


            self.update_stats(new_start, new_end)
            self.update()
            super().update()

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def hoverEnterEvent(self, event):
        edge_status = self.check_for_edge(event)

        if edge_status:
            self.is_hovered = False

        self.update(self.boundingRect())

    def hoverLeaveEvent(self, event):
        _ = self.check_for_edge(event)

        self.is_hovered = False
        self.edge_hovering = False
        self.selected_edge = None
        self.update(self.boundingRect())

    def highlight_on(self):
        self.is_selected = True
        self.update()

    def highlight_off(self):
        self.is_selected = False
        self.update()

    def on_selected(self):
        if self.isSelected() is True or self.is_selected is True:
            return True
        else:
            return False

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene_pos = self.sceneBoundingRect()
            new_start = QPointF(scene_pos.x(), scene_pos.y())
            new_end = QPointF(scene_pos.x() + scene_pos.width(), scene_pos.y() + scene_pos.height())
            self.update_stats(new_start, new_end)

        else:
            return value

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height, 4, 4)

        if self.on_selected():
            _pen = self._pen_selected

        elif self.is_hovered:
            _pen = self._pen_hover
            painter.setPen(_pen)
            painter.setBrush(QBrush(Qt.GlobalColor.red, Qt.BrushStyle.SolidPattern))
        else:
            _pen = self._pen_default

        painter.setPen(_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_outline.simplified())

        if self.selected_edge is not None:
            _rect_size = 10
            _pen = self._pen_hover
            painter.setBrush(QBrush(Qt.GlobalColor.red, Qt.BrushStyle.SolidPattern))

            if self.selected_edge == Edge.Top:
                painter.drawRect(-_rect_size // 2, -_rect_size // 2, _rect_size, _rect_size)
                painter.drawRect(int(self.width - (_rect_size // 2)), - _rect_size // 2, _rect_size, _rect_size)

            elif self.selected_edge == Edge.Bottom:
                painter.drawRect(int(self.width - (_rect_size // 2)), int(self.height - _rect_size // 2), _rect_size, _rect_size)
                painter.drawRect(-_rect_size // 2, int(self.height - _rect_size // 2), _rect_size, _rect_size)

            elif self.selected_edge == Edge.Left:
                painter.drawRect(-_rect_size // 2, -_rect_size // 2, _rect_size, _rect_size)
                painter.drawRect(-_rect_size // 2, int(self.height - _rect_size // 2), _rect_size, _rect_size)

            elif self.selected_edge == Edge.Right:
                painter.drawRect(int(self.width - (_rect_size // 2)), - _rect_size // 2, _rect_size, _rect_size)
                painter.drawRect(int(self.width - (_rect_size // 2)), int(self.height - _rect_size // 2), _rect_size, _rect_size)