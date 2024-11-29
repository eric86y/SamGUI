import uuid
from uuid import UUID
from PIL.ImageQt import ImageQt
from SamGui.Widgets.Buttons import MenuButton

from SamGui.Widgets.GraphicItems import AnnotationItem, AnchorPoint, BBoxRect, PixmapImage, MaskPreview
from SamGui.Controller import HeaderController, CanvasController
from SamGui.Widgets.Dialogs import ConfirmationWindow, NotificationWindow
from SamGui.Data import Tool, Label, Anchor, BBox, Mask, SegmentationData, AnchorState, BBoxLabel, \
    ProjectData, ZoomLevel, BBoxPosition, AnchorPosition
from SamGui.Widgets.ListWidgets import CanvasAnchorEntry, CanvasBBoxEntry, CanvasHierarchyEntry, ImageEntry
from SamGui.MVVM.viewmodel import SamViewModel
from SamGui.Utils import generate_alpha_mask, has_data
from PySide6.QtGui import QIcon, QBrush, QColor, QPen, QPixmap, QResizeEvent, QPainter, QImage
from PySide6.QtCore import Qt, Signal, QPoint, QPointF
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsItem,
    QListWidget,
    QListWidgetItem
)


class Header(QFrame):
    def __init__(self, controller: HeaderController, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("Header")
        self.setMinimumWidth(600)
        self.setMinimumHeight(120)
        self.controller = controller
        self.main_tools = MainTools(parent=self)
        self.canvas_tools = CanvasTools(parent=self)
        self.sam_tools = SamTools(parent=self)

        # bind signals
        self.main_tools.btn_new.clicked.connect(self.new_project)
        self.main_tools.btn_open.clicked.connect(self.load_image)
        self.main_tools.btn_import_project.clicked.connect(self.import_project)
        self.main_tools.btn_export_project.clicked.connect(self.export_project)

        self.canvas_tools.s_clear_canvas.connect(self.clear_canvas)
        self.canvas_tools.s_set_current_tool.connect(self.set_current_tool)
        self.canvas_tools.s_toggle_debug_view.connect(self.toggle_debug_view)
        self.sam_tools.s_on_run_sam.connect(self.run_sam)
        self.sam_tools.s_on_sam_settings.connect(self.open_sam_settings)

        # build layout
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.main_tools)
        self.layout.addWidget(self.canvas_tools)
        self.layout.addWidget(self.sam_tools)
        self.layout.setContentsMargins(10, 0, 0, 0)

        self.setLayout(self.layout)

        self.show()

    def new_project(self):
        self.controller.set_new_project()

    def load_image(self):
        self.controller.import_images()

    def import_annotations(self):
        self.controller.import_annotations()

    def save_annotations(self):
        self.controller.save_annotations()

    def import_project(self):
        self.controller.import_project()

    def export_project(self):
        self.controller.export_project()

    def export_masks(self):
        self.controller.export_masks()

    def clear_canvas(self):
        self.controller.clear_canvas()

    def set_current_tool(self, tool: Tool):
        self.controller.set_tool(tool)

    def toggle_debug_view(self):
        self.controller.toggle_debug()

    def run_sam(self):
        self.controller.run_sam()

    def open_sam_settings(self):
        self.controller.open_settings()


class MainTools(QFrame):
    def __init__(self, button_size: int = 42, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("ToolBox")
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(4)
        self.button_size = button_size
        self.setFixedHeight(96)
        self.setMaximumWidth(360)
        self.v_layout = QVBoxLayout()

        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_new = MenuButton(
            QIcon("SamGui/Assets/Textures/new_light.png"),
            QIcon("SamGui/Assets/Textures/new_hover.png"),
            width=self.button_size,
            height=self.button_size,
            toolip="New Project"
        )

        self.btn_open = MenuButton(
            QIcon("SamGui/Assets/Textures/load_files_btn.png"),
            QIcon("SamGui/Assets/Textures/load_files_btn_highlight.png"),
            width=self.button_size,
            height=self.button_size,
            toolip="Import Images"
        )

        self.btn_import_project = MenuButton(
            QIcon("SamGui/Assets/Textures/import_project_light.png"),
            QIcon("SamGui/Assets/Textures/import_project_light_hover.png"),
            width=self.button_size,
            height=self.button_size,
            toolip="Import Yolo Project"
        )

        self.btn_export_project = MenuButton(
            QIcon("SamGui/Assets/Textures/export_project_light.png"),
            QIcon("SamGui/Assets/Textures/export_project_light_hover.png"),
            width=self.button_size,
            height=self.button_size,
            toolip="Export Yolo Project"
        )

        # build layout
        self.layout.addWidget(self.btn_new)
        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_import_project)
        self.layout.addWidget(self.btn_export_project)

        self.label = QLabel("Main")
        self.label.setObjectName("ToolLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.v_layout.addLayout(self.layout)
        self.v_layout.addWidget(self.label)
        self.setLayout(self.v_layout)


class CanvasTools(QFrame):
    s_clear_canvas = Signal()
    s_set_current_tool = Signal(Tool)
    s_toggle_debug_view = Signal()

    def __init__(self, button_size: int = 42, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("ToolBox")
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(4)
        self.button_size = button_size
        self.setFixedHeight(96)
        self.active_tool = Tool.Selection

        # define icons
        self.select_tool_icon = QIcon("SamGui/Assets/Textures/select_tool_icon.png")
        self.select_tool_icon_hover = QIcon(
            "SamGui/Assets/Textures/select_tool_icon_hover.png"
        )

        self.anchor_tool_icon = QIcon("SamGui/Assets/Textures/anchor_light.png")
        self.anchor_tool_icon_hover = QIcon(
            "SamGui/Assets/Textures/anchor_light_hover.png"
        )

        self.bbox_tool_icon = QIcon("SamGui/Assets/Textures/bbox_tool_light.png")
        self.bbox_tool_icon_hover = QIcon(
            "SamGui/Assets/Textures/bbox_tool_light_hover.png"
        )

        self.debug_icon = QIcon("SamGui/Assets/Textures/debug.png")
        self.debug_icon_hover = QIcon("SamGui/Assets/Textures/debug_hover.png")

        # define buttons
        self.selection_tool_btn = MenuButton(
            self.select_tool_icon,
            self.select_tool_icon_hover,
            width=self.button_size,
            height=self.button_size,
            toolip="Selection Tool: Click and move objects"
        )

        self.anchor_tool_btn = MenuButton(
            self.anchor_tool_icon,
            self.anchor_tool_icon_hover,
            width=self.button_size,
            height=self.button_size,
            toolip="Anchor Tool: Place Anchors on the Canvas. Use left-click to place a foreground and "
            "right-click to place background anchor"
        )

        self.bbox_tool_btn = MenuButton(
            self.bbox_tool_icon,
            self.bbox_tool_icon_hover,
            width=self.button_size,
            height=self.button_size,
            toolip="BBox Tool: Draw a non-resizable BBox to the canvas using the the right mouse button"
        )

        self.debug_view_btn = MenuButton(
            self.debug_icon,
            self.debug_icon_hover,
            width=self.button_size,
            height=self.button_size,
            toolip="Debug Window"
        )

        # bind button actions
        self.selection_tool_btn.clicked.connect(self.set_select_tool)
        self.anchor_tool_btn.clicked.connect(self.set_anchor_tool)
        self.bbox_tool_btn.clicked.connect(self.set_bbox_tool)
        self.debug_view_btn.clicked.connect(self.toggle_debug_view)

        # Tool Label
        self.label = QLabel("Tools")
        self.label.setObjectName("ToolLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # build layout
        self.v_layout = QVBoxLayout()
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.selection_tool_btn)
        self.layout.addWidget(self.anchor_tool_btn)
        self.layout.addWidget(self.bbox_tool_btn)
        self.layout.addWidget(self.debug_view_btn)

        self.v_layout.addLayout(self.layout)
        self.v_layout.addWidget(self.label)
        self.setLayout(self.v_layout)

    def set_select_tool(self):
        self.active_tool = Tool.Selection
        self.selection_tool_btn.activate()
        self.anchor_tool_btn.deactivate()
        self.bbox_tool_btn.deactivate()

        self.s_set_current_tool.emit(self.active_tool)

    def set_anchor_tool(self):
        self.active_tool = Tool.Anchor

        self.anchor_tool_btn.activate()
        self.selection_tool_btn.deactivate()
        self.bbox_tool_btn.deactivate()

        self.s_set_current_tool.emit(self.active_tool)

    def set_bbox_tool(self):
        self.active_tool = Tool.BBOX

        self.bbox_tool_btn.activate()
        self.selection_tool_btn.deactivate()
        self.anchor_tool_btn.deactivate()

        self.s_set_current_tool.emit(self.active_tool)

    def toggle_debug_view(self):
        self.s_toggle_debug_view.emit()

    def get_active_tool(self):
        return self.active_tool


class SamTools(QFrame):
    s_on_run_sam = Signal()
    s_on_sam_settings = Signal()

    def __init__(self, button_size: int = 42, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("ToolBox")
        self.v_layout = QVBoxLayout()
        self.h_layout = QHBoxLayout()

        self.v_layout.setContentsMargins(0, 0, 0, 0)

        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(4)
        self.button_size = button_size
        self.setFixedHeight(96)
        self.active_tool = Tool.Selection
        self.label = QLabel("SAM")
        self.label.setObjectName("ToolLabel")

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # define icons
        self.run_icon = QIcon("SamGui/Assets/Textures/play_light.png")
        self.run_icon_hover = QIcon("SamGui/Assets/Textures/play_light_hover.png")
        self.settings_icon = QIcon("SamGui/Assets/Textures/settings.png")
        self.anchor_tool_icon_hover = QIcon("SamGui/Assets/Textures/settings_hover.png")

        # define buttons
        self.run_sam_btn = MenuButton(
            self.run_icon,
            self.run_icon_hover,
            width=self.button_size,
            height=self.button_size,
            toolip="Run SAM on manually placed annotations"
        )

        self.show_sam_settings_btn = MenuButton(
            self.settings_icon,
            self.anchor_tool_icon_hover,
            width=self.button_size,
            height=self.button_size,
        )

        # bind actions
        self.run_sam_btn.clicked.connect(self.run_sam)
        self.show_sam_settings_btn.clicked.connect(self.show_sam_settings)

        # build layout
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout = QVBoxLayout()
        self.layout.addWidget(self.run_sam_btn)
        self.layout.addWidget(self.show_sam_settings_btn)

        self.v_layout.addLayout(self.layout)
        self.v_layout.addWidget(self.label)
        self.setLayout(self.v_layout)

    def run_sam(self):
        self.s_on_run_sam.emit()

    def show_sam_settings(self):
        self.s_on_sam_settings.emit()


class CanvasHierarchyHeader(QFrame):
    sign_on_delete_hierarchy = Signal()

    def __init__(self, parent=None, label_text: str = "Elements", height: int = 48, add_delete: bool = True):
        super().__init__()
        self.parent = parent
        self.setObjectName("HierarchyHeader")
        self._label_text = label_text
        self.default_height = height
        self.setMaximumHeight(height)
        self.setMinimumWidth(240)
        self.setMaximumWidth(460)

        self.label = QLabel(self._label_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.delete_icon = QIcon("SamGui/Assets/Textures/delete_icon_light.png")
        self.delete_hover_icon = QIcon(
            "SamGui/Assets/Textures/delete_icon_light_hover.png"
        )

        self.btn_delete_hierarchy = MenuButton(
            self.delete_icon, self.delete_hover_icon, width=16, height=16
        )

        self.btn_delete_hierarchy.clicked.connect(self.clear_hierarchy)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)

        if add_delete:
            self.layout.addWidget(self.btn_delete_hierarchy)

        self.setLayout(self.layout)

    def set_text(self, text: str):
        self._label_text = text
        self.label.setText(f"{text}")

    def clear_hierarchy(self):
        self.sign_on_delete_hierarchy.emit()


class HierarchyHeader(QFrame):
    sign_on_delete_hierarchy = Signal()

    def __init__(self, parent=None, label_text: str = "Elements", height: int = 48, add_delete: bool = True):
        super().__init__()
        self.parent = parent
        self.setObjectName("HierarchyHeader")
        self._label_text = label_text
        self.default_height = height
        self.setMaximumHeight(height)
        self.setMinimumWidth(240)
        self.setMaximumWidth(460)

        self.label = QLabel(self._label_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.delete_icon = QIcon("SamGui/Assets/Textures/delete_icon_light.png")
        self.delete_hover_icon = QIcon(
            "SamGui/Assets/Textures/delete_icon_light_hover.png"
        )
        self.btn_delete_hierarchy = MenuButton(
            self.delete_icon, self.delete_hover_icon, width=16, height=16
        )

        self.btn_delete_hierarchy.clicked.connect(self.clear_hierarchy)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)

        if add_delete:
            self.layout.addWidget(self.btn_delete_hierarchy)

        self.setLayout(self.layout)

    def set_text(self, text: str):
        self._label_text = text
        self.label.setText(f"{text}")

    def clear_hierarchy(self):
        self.sign_on_delete_hierarchy.emit()


class ImportedImageList(QFrame):
    def __init__(self, view_model: SamViewModel):
        super().__init__()
        self.setObjectName("SideBox")
        self.view_model = view_model
        self.header = HierarchyHeader(label_text="Imported Images")
        self.widget_list = WidgetList()

        # connect signals
        self.header.sign_on_delete_hierarchy.connect(self.delete_images)
        self.widget_list.s_on_item_selected.connect(self.handle_item_selection)
        self.view_model.s_dataChanged.connect(self.update_data)

        # build layout
        self.setMinimumWidth(260)
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.header)
        self.v_layout.addWidget(self.widget_list)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(0)
        self.setLayout(self.v_layout)

    def delete_images(self):
        project_data = self.view_model.get_data()

        if project_data.data is not None:
            dialog = ConfirmationWindow("Deleting all Images in Project",
                                        "You are going to delete all images including all manually created annotations in the project. Are you sure?")

            if dialog.exec():
                self.view_model.delete_images()

    def handle_item_selection(self, guid: UUID):
        self.view_model.select_image_by_guid(guid)

    def add_data(self, project_data: ProjectData):
        self.widget_list.clear()

        if has_data(project_data.data):
            for k, data in project_data.data.items():
                item = QListWidgetItem(self.widget_list)
                entry = ImageEntry(data.guid, data.file_name)
                entry.s_on_export_annotations.connect(self.export_annotations)
                entry.s_on_mask_export_cropped.connect(self.export_cropped_mask)
                entry.s_on_mask_export.connect(self.export_mask)
                entry.s_on_selected.connect(self.select_item)
                item.setSizeHint(entry.sizeHint())

                self.widget_list.addItem(item)
                self.widget_list.setItemWidget(item, entry)

            for idx in range(self.widget_list.count()):
                entry = self.widget_list.itemWidget(self.widget_list.item(idx))
                if idx % 2 == 0:
                    _qBrush = QBrush(QColor("#1e1a3d"))
                    if isinstance(entry, ImageEntry):
                        entry.set_dark_background()
                        self.widget_list.item(idx).setBackground(_qBrush)
                else:
                    _qBrush = QBrush(QColor("#292951"))
                    if isinstance(entry, ImageEntry):
                        entry.set_light_background()
                        self.widget_list.item(idx).setBackground(_qBrush)

    def update_data(self, data: ProjectData):
        self.widget_list.clear()
        self.add_data(data)

    def delete_annotations(self, image_guid: UUID):
        self.view_model.delete_annotations(image_guid)

    def export_annotations(self, image_guid: UUID):
        self.view_model.export_yolo_annotations(image_guid)

    def export_mask(self, image_guid: UUID):
        self.view_model.export_mask(image_guid)

    def export_cropped_mask(self, image_guid: UUID):
        self.view_model.export_masks_cropped(image_guid)

    def select_item(self, image_guid: UUID):
        """
        TODO: Maybe some style overrides
        """

class MainHierarchy(QFrame):
    def __init__(self, view_model: SamViewModel):
        super(MainHierarchy, self).__init__()
        self.setObjectName("MainHierarchy")
        self.view_model = view_model
        self.image_list = ImportedImageList(self.view_model)

        # build layout
        self.setMinimumWidth(320)
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.image_list)
        self.v_layout.setSpacing(10)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.v_layout)


class WidgetList(QListWidget):
    s_on_item_selected = Signal(UUID)
    s_on_item_entered = Signal()
    s_on_item_left = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setObjectName("WidgetList")
        self.setMinimumWidth(240)
        self.setMaximumWidth(460)
        self.setContentsMargins(0, 0, 0, 0)
        self.itemClicked.connect(self.on_item_clicked)
        self.itemEntered.connect(self.on_item_entered)

        self.v_scrollbar = self.verticalScrollBar()

        self.v_scrollbar.setStyleSheet(
            """
            QScrollBar:vertical {
                border: none;
                background: rgb(45, 45, 68);
                width: 25px;
                margin: 10px 5px 15px 10px;
                border-radius: 0px;
             }

            QScrollBar::handle:vertical {
                border: 2px solid #ffad00;
                background-color: #ffad00;
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover{	
                background-color: #ffad00;
            }
            QScrollBar::handle:vertical:pressed {	
                background-color: #ffad00;
            }

            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-line:vertical {
                height: 0px;
            }

            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            """
        )

        self.setStyleSheet("""
            QListWidget::item:selected {
                    background-color: #ffad00;
                }
        """)


    def on_item_clicked(self, item: QListWidgetItem):
        _list_item_widget = self.itemWidget(item)

        if isinstance(_list_item_widget, ImageEntry):
            _qBrush = QBrush(QColor("#292951"))
            #item.setBackground(_qBrush)

        if isinstance(_list_item_widget, CanvasHierarchyEntry) or isinstance(_list_item_widget, ImageEntry):
            _guid = _list_item_widget.guid
            self.s_on_item_selected.emit(_guid)

    def on_item_entered(self, item: QListWidgetItem):
        self.s_on_item_entered.emit()

    def on_item_left(self, item: QListWidgetItem):
        self.s_on_item_left.emit()


class CanvasHierarchy(QFrame):
    def __init__(self, controller: CanvasController):
        super().__init__()
        self.setObjectName("CanvasHierarchy")
        self.controller = controller
        self.delete_box = ConfirmationWindow("Confirm canvas deletion..", "Delete Canvas Element?")
        self.header = CanvasHierarchyHeader(label_text="Annotations", height=56)
        self.element_list = WidgetList(self)

        self.anchor_items = []
        self.bbox_items = []

        # bind signals
        self.header.sign_on_delete_hierarchy.connect(self.delete_annotations)
        self.controller.s_add_anchor.connect(self.add_anchor)
        self.controller.s_add_bbox.connect(self.add_bbox)
        self.controller.s_clear_data.connect(self.clear)
        self.element_list.s_on_item_selected.connect(self.select_item)

        # build layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.element_list)
        self.setLayout(self.layout)

    def clear(self):
        self.element_list.clear()

    def delete_annotations(self):
        self.clear()
        self.controller.delete_all_canvas_annotations()

    def add_anchor(self, anchor: Anchor):
        self.anchor_items.append(anchor)

        entry = CanvasAnchorEntry(
            anchor.guid, self.controller,
            label="Anchor",
            label_class=anchor.class_id,
            parent=self)

        self.update_hierarchy(entry)

    def add_bbox(self, bbox: BBox):
        self.bbox_items.append(bbox)

        entry = CanvasBBoxEntry(
            bbox.guid,
            self.controller,
            label=bbox.name,
            parent=self)

        self.update_hierarchy(entry)

    def select_item(self, guid: UUID):
        self.controller.select_item(guid)

        for idx in range(self.element_list.count()):
            entry = self.element_list.itemWidget(self.element_list.item(idx))
            if isinstance(entry, CanvasHierarchyEntry):
                if entry.guid == guid:
                    entry.set_light_background()
                else:
                    entry.set_dark_background()

    def update_hierarchy(self, entry: CanvasHierarchyEntry):
        _list_widget = QListWidgetItem(self.element_list)
        _list_widget.setSizeHint(entry.sizeHint())
        self.element_list.addItem(_list_widget)
        self.element_list.setItemWidget(_list_widget, entry)

        for idx in range(self.element_list.count()):
            entry = self.element_list.itemWidget(self.element_list.item(idx))
            if idx % 2 == 0:
                _qBrush = QBrush(QColor("#1e1a3d"))
                if isinstance(entry, CanvasHierarchyEntry):
                    entry.set_dark_background()
                    self.element_list.item(idx).setBackground(_qBrush)
            else:
                _qBrush = QBrush(QColor("#292951"))
                if isinstance(entry, CanvasHierarchyEntry):
                    entry.set_light_background()
                    self.element_list.item(idx).setBackground(_qBrush)


class CanvasElements(QWidget):
    def __init__(self, controller: CanvasController, parent=None):
        super().__init__()
        self.parent = parent
        self.setObjectName("CanvasElements")
        self.setMinimumWidth(300)
        self.controller = controller
        self.canvas_hierarchy = CanvasHierarchy(self.controller)

        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.addWidget(self.canvas_hierarchy)
        self.setLayout(self.v_layout)

    def clear(self):
        self.canvas_hierarchy.clear()


class Canvas(QFrame):
    sign_on_item_added = Signal(QGraphicsItem)

    def __init__(self, canvas_controller: CanvasController, width: int = 1200, height: int = 800, parent=None):
        super().__init__()

        self.setObjectName("Canvas")
        self.parent = parent
        self.controller = canvas_controller
        self.default_width = width
        self.default_height = height

        self.current_width = self.default_width
        self.current_height = self.default_height

        self.gr_scene = SAMGraphicsScene(self)
        self.view = QDMGraphicsView(self.gr_scene)
        self.view.setScene(self.gr_scene)
        self.view.s_update_zoom.connect(self.update_zoom)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 0, 4, 4)
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        # binding input actions
        self.gr_scene.s_right_mouse_press.connect(self.handle_right_click)
        self.gr_scene.s_right_mouse_release.connect(self.handle_right_release)
        self.gr_scene.s_left_mouse_press.connect(self.handle_left_click)
        self.gr_scene.s_update_bbox_position.connect(self.handle_bbox_position)
        self.gr_scene.s_update_anchor_position.connect(self.handle_anchor_position)
        self.gr_scene.s_clear_selections.connect(self.clear_selections)

        self.controller.s_select_canvas_item.connect(self.select_item)
        self.controller.s_clear_data.connect(self.clear_canvas)
        self.controller.s_delete_elements.connect(self.clear_canvas)
        self.controller.s_toggle_anchor_state.connect(self.toggle_anchor_state)


        self._tmp_start_point = None
        self._tmp_end_point = None

        """
        Maybe not all references are needed.
        The guid is used to store the zoom factor on the current image, so that the use doesn't have to adjust the scaling every time
        when switching between images in the Image Hierarchy
        """
        self.current_image_guid = None
        self.current_image = None  # QGraphicsPixmapItem
        self.current_mask = None  # Mask item
        self.hidden_items = []

        self.show()
        self.canvas_objects = []
        self.current_tool = Tool

    def handle_bbox_position(self, bbox: BBoxRect):
        position = BBoxPosition(bbox.guid, bbox.start_point.x(), bbox.start_point.y(), bbox.width, bbox.height)
        self.controller.s_update_bbox_position.emit(position)

    def handle_anchor_position(self, anchor: AnchorPoint):
        position = AnchorPosition(anchor.guid, anchor.x_pos, anchor.y_pos)
        self.controller.s_update_anchor_position.emit(position)


    def resizeEvent(self, event):
        if isinstance(event, QResizeEvent):
            _new_size = event.size()
            self.current_width = _new_size.width()
            self.current_height = _new_size.height()

    def update_zoom(self, value: float):
        if self.current_image_guid is not None:
            self.controller.update_zoom(self.current_image_guid, value)


    def handle_left_click(self, qpoint):
        if self.current_tool == Tool.Selection:
            _selected_items = self.gr_scene.selectedItems()

        if self.current_tool == Tool.Anchor:
            _anchor = Anchor(
                guid=uuid.uuid1(),
                class_id=Label.foreground,
                active=True,
                x=qpoint.x(),
                y=qpoint.y()
            )
            self.add_anchor(_anchor)


    def handle_right_click(self, qpointf: QPointF):
        if self.current_tool == Tool.BBOX:
            self.gr_scene.freeze_items()
            self.view.enable_rubberband()

            self._tmp_start_point = qpointf

    def handle_right_release(self, qpointf: QPointF):
        if self.current_tool == Tool.Anchor:
            _anchor = Anchor(
                guid=uuid.uuid1(),
                class_id=Label.background,
                active=True,
                x=int(qpointf.x()),
                y=int(qpointf.y())
            )
            self.add_anchor(_anchor)

        if self.current_tool == Tool.BBOX:
            self._tmp_end_point = qpointf

            # handles the case of dragging the bbox from right to left
            if self._tmp_end_point.x() < self._tmp_start_point.x():
                start_point = self._tmp_end_point
                end_point = self._tmp_start_point

            else:
                start_point = self._tmp_start_point
                end_point = self._tmp_end_point

            if start_point is not None and end_point is not None:
                x = start_point.x()
                y = start_point.y()
                w = end_point.x() - x
                h = end_point.y() - y

                _bbox = BBox(
                    guid=uuid.uuid1(),
                    name="BBox",
                    active=True,
                    x=x,
                    y=y,
                    w=w,
                    h=h
                )

                bbox = BBoxRect(_bbox.guid, self.controller, self._tmp_start_point, self._tmp_end_point)
                bbox.set_name("BBox")
                self.canvas_objects.append(bbox)
                self.gr_scene.add_item(bbox, z_order=5)
                self.controller.add_canvas_bbox(_bbox)
                self.view.disable_rubberband()
                self.gr_scene.unfreeze_items()
                self._tmp_start_point = None
                self._tmp_end_point = None

    def clear_selections(self):
        _canvas_items = self.gr_scene.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _canvas_items:
            if isinstance(_item, AnchorPoint):
                _item.highlight_off()
                _item.setSelected(False)

    def clear_canvas(self):
        self.hidden_items.clear()

        for item in self.canvas_objects:
            self.gr_scene.remove_item(item)

        self.canvas_objects.clear()

        _canvas_items = self.gr_scene.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _canvas_items:
            self.gr_scene.remove_item(_item)


    def set_image(self, data: SegmentationData):
        self.clear_canvas()
        self.view.reset_scale()

        _pixmap_image = PixmapImage(data.guid, data.file_path, self.controller)
        self.current_image = _pixmap_image
        self.current_image_guid = data.guid
        self.current_mask = data.mask

        _pixmap_image.update_position(data.x, data.y)
        self.gr_scene.add_item(_pixmap_image, z_order=0)
        self.view.reset_scrollbars()
        self.view.scale_view(data.zoom)


    def show_mask(self, mask: Mask):
        alpha_image = generate_alpha_mask(mask.image)
        qt_image = ImageQt(alpha_image)
        q_image = QImage(qt_image)
        pixmap = QPixmap.fromImage(q_image)
        mask_item = MaskPreview(mask.guid, mask.image, pixmap, self.controller)
        mask_item.update_position(mask.x, mask.y)

        self.gr_scene.add_item(mask_item, z_order=2)
        self.current_mask = mask_item

    def clear_annotations(self):
        _canvas_items = self.gr_scene.items(order=Qt.SortOrder.AscendingOrder)
        for _item in _canvas_items:
            if isinstance(_item, AnnotationItem):
                self.gr_scene.remove_item(_item)

    def set_current_tool(self, tool: Tool):
        self.current_tool = tool

    def add_anchor(self, anchor: Anchor) -> None:
        _anchor_point = AnchorPoint(
            guid=anchor.guid,
            controller=self.controller,
            x_pos=anchor.x,
            y_pos=anchor.y,
            class_id=anchor.class_id
        )

        self.canvas_objects.append(_anchor_point)
        self.gr_scene.add_item(_anchor_point, z_order=5)
        self.controller.add_canvas_anchor(anchor)

    def populate_anchor(self, anchor: Anchor):
        _anchor_point = AnchorPoint(
            guid=anchor.guid,
            controller=self.controller,
            x_pos=anchor.x,
            y_pos=anchor.y,
            class_id=anchor.class_id
        )

        self.canvas_objects.append(_anchor_point)
        self.gr_scene.add_item(_anchor_point, z_order=5)


    def populate_bbox(self, bbox: BBox):
        _bbox = BBoxRect(
            guid=bbox.guid,
            controller=self.controller,
            start_point=QPointF(bbox.x, bbox.y),
            end_point=QPointF(bbox.x + bbox.w, bbox.y + bbox.h)
        )

        self.canvas_objects.append(_bbox)
        self.gr_scene.add_item(_bbox, z_order=5)
        #.setVisible(True)
        #_bbox.update()

    def select_item(self, guid: UUID):
        _canvas_items = self.gr_scene.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _canvas_items:
            if isinstance(_item, AnchorPoint):
                if _item.guid == guid:
                    _item.highlight_on()
                else:
                    _item.highlight_off()

            elif isinstance(_item, BBoxRect):
                if _item.guid == guid:
                    _item.highlight_on()
                else:
                    _item.highlight_off()

    def toggle_anchor_state(self, state: AnchorState):
        _canvas_items = self.gr_scene.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _canvas_items:
            if isinstance(_item, AnchorPoint):
                if _item.guid == state.guid:

                    if not state.active:
                        self.hidden_items.append(_item)
                        self.gr_scene.remove_item(_item)
                    else:
                        for hidden_item in self.hidden_items:
                            if hidden_item.guid == state.guid:
                                self.gr_scene.add_item(hidden_item, z_order=5)
                                self.hidden_items.remove(hidden_item)


class CanvasPanel(QWidget):
    def __init__(self, view_model: SamViewModel, controller: HeaderController, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.view_model = view_model
        self.header_controller = controller
        self.canvas_controller = CanvasController()
        self.setObjectName("CanvasPanel")
        self.canvas = Canvas(self.canvas_controller)
        self.canvas_elements = CanvasElements(self.canvas_controller, self)

        # bind actions
        self.view_model.s_dataSelected.connect(self.select_image)
        self.view_model.s_dataChanged.connect(self.change_data)

        self.canvas_controller.s_add_anchor.connect(self.add_anchor)
        self.canvas_controller.s_add_bbox.connect(self.add_bbox)
        self.canvas_controller.s_delete_element.connect(self.delete_element)
        self.canvas_controller.s_delete_elements.connect(self.delete_annotations)
        self.canvas_controller.s_update_bbox_label.connect(self.update_bbox_label)
        self.canvas_controller.s_update_anchor_position.connect(self.update_anchor_position)
        self.canvas_controller.s_update_bbox_position.connect(self.update_bbox_position)
        self.canvas_controller.s_update_zoom.connect(self.update_zoom_level)

        self.header_controller.s_select_tool.connect(self.set_tool)

        # build layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.canvas_elements)
        self.setLayout(self.layout)

        self.current_image_guid = None

    def select_image(self, data: SegmentationData):
        self.canvas.clear_canvas()
        self.canvas_elements.canvas_hierarchy.clear()
        self.canvas_controller.clear_data()
        self.canvas.set_image(data)
        self.current_image_guid = data.guid

        for anchor in data.anchors:
            self.canvas.populate_anchor(anchor)
            self.canvas_elements.canvas_hierarchy.add_anchor(anchor)

        for bbox in data.bboxes:
            self.canvas.populate_bbox(bbox)
            self.canvas_elements.canvas_hierarchy.add_bbox(bbox)

        if data.mask is not None and data.mask.image is not None:
            self.canvas.show_mask(data.mask)


    def change_data(self, project: ProjectData):
        if len(project.data) == 0:
            self.canvas.clear_canvas()
            self.canvas_elements.clear()

        for _guid, _data in project.data.items():
            if _guid == self.current_image_guid:
                self.select_image(_data)

    def set_tool(self, tool: Tool):
        self.canvas.set_current_tool(tool)

    def add_anchor(self, anchor: Anchor):
        if self.current_image_guid is not None:
            self.view_model.add_anchor(self.current_image_guid, anchor)
        else:
            dialog = NotificationWindow("No Image selected", "Canvas does not an image. Please import and select an image.")
            dialog.exec()

    def add_bbox(self, bbox: BBox):
        if self.current_image_guid is not None:
            self.view_model.add_bbox(self.current_image_guid, bbox)
        else:
            dialog = NotificationWindow("No Data in Project", "Project contains no image. Please import an image.")
            dialog.exec()

    def update_bbox_label(self, update: BBoxLabel):
        self.view_model.update_bbox_label(self.current_image_guid, update.guid, update.label)

    def update_anchor_position(self, position: AnchorPosition):
        if self.current_image_guid is not None:
            self.view_model.update_anchor_position(self.current_image_guid, position)

    def update_bbox_position(self, position: BBoxPosition):
        if self.current_image_guid is not None:
            self.view_model.update_bbox_position(self.current_image_guid, position)

    def update_zoom_level(self, zoom_level: ZoomLevel):
        self.view_model.update_zoom_level(zoom_level)

    def delete_element(self, guid: UUID):
        self.view_model.delete_item_by_guid(guid)

    def delete_annotations(self):
        self.view_model.delete_annotations(self.current_image_guid)


class SAMGraphicsScene(QGraphicsScene):
    s_left_mouse_press = Signal(QPointF)
    s_left_mouse_release = Signal()
    s_update_anchor_position = Signal(AnchorPoint)
    s_update_bbox_position = Signal(BBoxRect)
    s_right_mouse_press = Signal(QPointF)
    s_right_mouse_release = Signal(QPointF)
    s_update_image_position = Signal(PixmapImage)
    s_clear_selections = Signal()

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._background_color = QColor("#393939")
        self.scene_width = 3200
        self.scene_height = 3200
        self.set_scene(self.scene_width, self.scene_height)

        self._line_color = QColor("#2f2f2f")
        self._pen_light = QPen(self._line_color)
        self._pen_light.setWidth(10)

        self._bg_image = QPixmap("SamGui/Assets/Textures/background_dot.png")
        self.setBackgroundBrush(self._bg_image)

    def set_scene(self, width: int, height: int) -> None:
        self.setSceneRect(0, 0, width, height)

    def add_item(self, item: QGraphicsItem, z_order: int):
        item.setZValue(z_order)
        self.addItem(item)

    def freeze_items(self):
        _items = self.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _items:
            _item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)


    def unfreeze_items(self):
        _items = self.items(order=Qt.SortOrder.AscendingOrder)

        for _item in _items:
            _item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def remove_item(self, item: QGraphicsItem):
        self.removeItem(item)

    def clear_masks(self):
        _items = self.items()

        for _item in _items:
            if isinstance(_item, MaskPreview):
                self.remove_item(_item)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            print("Deleting stuff")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            q_pointf = e.buttonDownScenePos(Qt.MouseButton.RightButton)

            self.s_right_mouse_press.emit(q_pointf)
            super().mousePressEvent(e)

        elif e.button() == Qt.MouseButton.LeftButton:
            if len(self.selectedItems()) == 0:
                self.s_clear_selections.emit()

            q_pointf = e.buttonDownScenePos(Qt.MouseButton.LeftButton)
            self.s_left_mouse_press.emit(q_pointf)
            super().mousePressEvent(e)


    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            q_pointf = e.scenePos()


            self.s_right_mouse_release.emit(q_pointf)
            super().mouseReleaseEvent(e)

        elif e.button() == Qt.MouseButton.LeftButton:
            self.s_left_mouse_release.emit()
            super().mouseReleaseEvent(e)
        else:
            super().mouseReleaseEvent(e)


class QDMGraphicsView(QGraphicsView):
    s_update_zoom = Signal(float)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(parent)
        self.setObjectName("GraphicsView")
        self.scene = scene
        self.setScene(self.scene)

        self.zoom_in_factor = 1.25
        self.zoom = 0
        self.zoom_step = 1
        self.zoom_range = [-5, 5]

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.default_scrollbar_policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        self.setHorizontalScrollBarPolicy(self.default_scrollbar_policy)
        self.setVerticalScrollBarPolicy(self.default_scrollbar_policy)

        self.verticalScrollBar().setSliderPosition(1)
        self.horizontalScrollBar().setSliderPosition(1)

        self.v_scrollbar = self.verticalScrollBar()
        self.h_scrollbar = self.horizontalScrollBar()

        self.v_scrollbar.setStyleSheet(
            """
                QScrollBar:vertical {
                border: none;
                background: rgb(45, 45, 68);
                width: 25px;
                margin: 10px 5px 15px 10px;
                border-radius: 0px;
             }

            QScrollBar::handle:vertical {
                border: 2px solid #ffad00;
                background-color: #ffad00;
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover{	
                background-color: #ffad00;
            }
            QScrollBar::handle:vertical:pressed {	
                background-color: #ffad00;
            }

            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-line:vertical {
                height: 0px;
            }

            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            """
        )

        self.h_scrollbar.setStyleSheet(
            """
            QScrollBar:horizontal {
               border: none;
                background: rgb(45, 45, 68);
                height: 30px;
                margin: 10px 10px 10px 10px;
                border-radius: 0px;
            }
            QScrollBar::handle:horizontal {
                border: 2px solid #ffad00;
                background-color: #ffad00;
                min-width: 30px;
                border-radius: 3px;
            }
            QScrollBar::add-line:horizontal {
                width: 0px;
            }
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
            {
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
            {
                background: none;
            }
        """
        )

    def enable_rubberband(self):
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def disable_rubberband(self):
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def hide_scrollbars(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def show_scrollbars(self):
        self.setHorizontalScrollBarPolicy(self.default_scrollbar_policy)
        self.setVerticalScrollBarPolicy(self.default_scrollbar_policy)

    def reset_scrollbars(self):
        self.h_scrollbar.setValue(0)
        self.v_scrollbar.setValue(0)

    def wheelEvent(self, event):
        event_pos = event.globalPosition()
        zoom_out_factor = 1 / self.zoom_in_factor

        if event.angleDelta().y() > 0:
            if not self.zoom > 5:
                zoom_factor = self.zoom_in_factor
                self.zoom += self.zoom_step
                self.scale(zoom_factor, zoom_factor)
        else:
            if not self.zoom < -5:
                zoom_factor = zoom_out_factor
                self.zoom -= self.zoom_step
                self.scale_view(zoom_factor)

        new_position = self.mapToScene(event.globalPosition().toPoint())
        move_delta = new_position - event_pos
        self.translate(move_delta.x(), move_delta.y())


    def scale_view(self, factor: float) -> None:
        self.scale(factor, factor)

    def reset_scale(self):
        self.zoom = 0
        self.resetTransform()