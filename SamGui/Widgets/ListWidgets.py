from uuid import UUID
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal
from SamGui.Controller import CanvasController
from SamGui.Widgets.Buttons import MenuButton
from SamGui.Widgets.Dialogs import TexInputDialog
from SamGui.Data import Label
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QRadioButton


class ImageEntry(QWidget):
    s_on_mask_export = Signal(UUID)
    s_on_mask_export_cropped = Signal(UUID)
    s_on_export_annotations = Signal(UUID)
    s_on_annotation_delete = Signal(UUID)
    s_on_selected = Signal(UUID)

    def __init__(self, guid: UUID, name: str, parent=None):
        super().__init__(parent)
        self.guid = guid
        self.name = name
        self.parent = parent
        self.is_dark = True
        self.label = QLabel(self.name)

        self.export_annotation_icon = QIcon("SamGui/Assets/Textures/save-disc.png")
        self.export_annotation_icon_hover = QIcon("SamGui/Assets/Textures/save-disc_highlight.png")

        self.export_icon = QIcon("SamGui/Assets/Textures/export_masks_btn.png")
        self.export_icon_hover = QIcon("SamGui/Assets/Textures/export_masks_btn_hover.png")

        self.export_cropped_icon = QIcon("SamGui/Assets/Textures/export_bboxes_btn.png")
        self.export_cropped_icon_hover = QIcon("SamGui/Assets/Textures/export_bboxes_btn_hover.png")

        self.delete_icon = QIcon("SamGui/Assets/Textures/delete_icon_light.png")
        self.delete_hover_icon = QIcon("SamGui/Assets/Textures/delete_icon_light_hover.png")

        self.btn_export_annotations = MenuButton(
            self.export_annotation_icon,
            self.export_annotation_icon_hover,
            width=24,
            height=24,
            object_name="listButton",
            toolip="Export YOLO annotation"
        )

        self.btn_export = MenuButton(
            self.export_icon,
            self.export_icon_hover,
            width=24,
            height=24,
            object_name="listButton",
            toolip="Export entire mask"
        )

        self.btn_export_cropped = MenuButton(
            self.export_cropped_icon,
            self.export_cropped_icon_hover,
            width=24,
            height=24,
            object_name="listButton",
            toolip="Export cropped areas based on BBoxes"
        )

        self.delete_btn = MenuButton(
            self.delete_icon,
            self.delete_hover_icon,
            width=24,
            height=24,
            object_name="listButton",
            toolip="Delete Annotations"
        )

        # bind signals
        self.btn_export_annotations.clicked.connect(self.export_yolo_annotations)
        self.btn_export.clicked.connect(self.export_mask)
        self.btn_export_cropped.clicked.connect(self.export_cropped_mask)
        self.delete_btn.clicked.connect(self.delete_annotations)

        # build layout
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.btn_export_annotations)
        self.h_layout.addWidget(self.btn_export)
        self.h_layout.addWidget(self.btn_export_cropped)
        self.h_layout.addWidget(self.delete_btn)

        self.setLayout(self.h_layout)

        self.setStyleSheet("""
                    background-color: #1e1a3d;
                    color: #ffffff;

                    QToolTip { 
                       background-color: #1e1a3d; 
                       color: #000000; 
                       border: white solid 1px
                            }
                """)

    def export_yolo_annotations(self):
        self.s_on_export_annotations.emit(self.guid)

    def export_mask(self):
        self.s_on_mask_export.emit(self.guid)

    def export_cropped_mask(self):
        self.s_on_mask_export_cropped.emit(self.guid)

    def delete_annotations(self):
        self.s_on_annotation_delete.emit(self.guid)


    def set_dark_background(self):
        self.is_dark = True

        self.setStyleSheet("""
            background-color: #1e1a3d;
        """)

        self.label.setStyleSheet("""
            background-color: #1e1a3d;
        """)

        self.btn_export_annotations.setStyleSheet("""
            background-color: #1e1a3d;
        """)

        self.btn_export.setStyleSheet("""
            background-color: #1e1a3d;
        """)

        self.btn_export_cropped.setStyleSheet("""
            background-color: #1e1a3d;
        """)

        self.delete_btn.setStyleSheet("""
            background-color: #1e1a3d;
        """)

    def set_light_background(self):
        self.is_dark = False
        self.setStyleSheet("""
                    background-color: #292951;
        """)
        self.label.setStyleSheet("""
                    background-color: #292951;
                        """)

        self.btn_export_annotations.setStyleSheet("""
                    background-color: #292951;
                """)

        self.btn_export.setStyleSheet("""
                    background-color: #292951;
                """)

        self.btn_export_cropped.setStyleSheet("""
                    background-color: #292951;
                """)

        self.delete_btn.setStyleSheet("""
                    background-color: #292951;
                """)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setStyleSheet("""
            background-color: #253363;
        """)
        self.label.setStyleSheet("""
            background-color: #253363;
        """)


    def leaveEvent(self, event):
        if self.is_dark:
            self.set_dark_background()
        else:
            self.set_light_background()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.label.setStyleSheet("""
                    background-color: #253363;
                """)

        self.s_on_selected.emit(self.guid)


class CanvasHierarchyEntry(QWidget):
    s_on_delete_item = Signal(UUID)

    def __init__(
            self,
            guid: UUID,
            controller: CanvasController,
            label: str = "Annotation",
            parent=None):

        super(CanvasHierarchyEntry, self).__init__(parent)
        self.parent = parent  # instance of CanvasElements
        self.controller = controller
        self.setObjectName("HierarchyEntry")
        self.guid = guid
        self._active = True
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.setMinimumWidth(200)
        self.setMaximumWidth(460)

        self.visibility_icon = QIcon("SamGui/Assets/Textures/eye_light.png")
        self.visibility_hover_icon = QIcon("SamGui/Assets/Textures/eye_light_hover.png")
        self.hidden_icon = QIcon("SamGui/Assets/Textures/eye_light_hidden.png")
        self.hidden_hover_icon = QIcon("SamGui/Assets/Textures/eye_light_hidden_hover.png")

        self.delete_icon = QIcon("SamGui/Assets/Textures/delete_icon_light.png")
        self.delete_hover_icon = QIcon("SamGui/Assets/Textures/delete_icon_light_hover.png")

        self.visibility_btn = MenuButton(self.visibility_icon, self.visibility_hover_icon, object_name="listButton")
        self.delete_btn = MenuButton(self.delete_icon, self.delete_hover_icon, object_name="listButton")

        self.delete_btn.setToolTip("Delete Annotation")
        self.visibility_btn.setToolTip("Deactivate Annotation")

        # bind buttons
        self.visibility_btn.clicked.connect(self.toggle_visibility)
        self.delete_btn.clicked.connect(self.delete_item)

        self.setStyleSheet("""
            QLabel {
                padding-left: 10px; 
            }
            
            QToolTip { 
               background-color: #1e1a3d; 
               color: #ffffff; 
               border: white solid 1px
                    }
        """)

    def toggle_visibility(self):
        print(f"Visibility!?, {type(self)}")
        self._active = not self._active

        if self._active:
            _icon = self.visibility_icon
            _icon_hover = self.visibility_hover_icon
        else:
            _icon = self.hidden_icon
            _icon_hover = self.hidden_hover_icon

        self.visibility_btn.set_icon(_icon)
        self.visibility_btn.set_hover_icon(_icon_hover)

        if isinstance(self, CanvasAnchorEntry):
            self.controller.toggle_anchor_state(self.guid, self._active)

        if isinstance(type(self), CanvasBBoxEntry):
            self.controller.toggle_bbox_state(self.guid, self._active)

        self.update()

    def delete_item(self):
        self.controller.delete_canvas_annotation(self.guid)

    def set_dark_background(self):
        self.label.setStyleSheet("""
                    background-color: #1e1a3d;
                    
                     QRadioButton {
                        background-color: #1e1a3d;
                    }
                """)

        self.delete_btn.setStyleSheet(
            """
            background-color: #1e1a3d;
            """
        )

        self.visibility_btn.setStyleSheet(
            """
            background-color: #1e1a3d;
            """
        )

    def set_light_background(self):
        self.label.setStyleSheet("""
            background-color: #292951;
            
            QRadioButton {
                background-color: #292951;
            }
                        """)

        self.delete_btn.setStyleSheet(
            """
            background-color: #292951;
            """
        )

        self.visibility_btn.setStyleSheet(
            """
            background-color: #292951;
            """
        )


class CanvasAnchorEntry(CanvasHierarchyEntry):
    def __init__(
            self,
            guid: UUID,
            controller: CanvasController,
            label: str = "Anchor",
            label_class: Label = Label.foreground,
            parent=None):

        super().__init__(guid, controller, label, parent)
        self.parent = parent
        self.controller = controller
        self.guid = guid
        self.label_class = label_class

        self.foreground_class_image = "SamGui/Assets/Textures/label_fg_toggle.png"
        self.background_class_image = "SamGui/Assets/Textures/label_bg_toggle.png"

        self.class_toggle = QRadioButton(self)
        self.class_toggle.setFixedWidth(16)
        self.class_toggle.setFixedHeight(16)
        self.class_toggle.setChecked(True if self.label_class == Label.background else False)
        self.class_toggle.clicked.connect(self.switch_label)

        if self.label_class == Label.background:
            self.class_toggle.setChecked(True)
            self.class_toggle.setToolTip("Toggle label to foreground")
            #self.class_toggle.setStyleSheet(""" QRadioButton::indicator:checked:pressed { background-image : url(SamGui/Assets/Textures/label_fg_toggle.png; } """)
        else:
            self.class_toggle.setChecked(False)
            self.class_toggle.setToolTip("Toggle label to background")
            #self.class_toggle.setStyleSheet(""" QRadioButton::indicator { background-image : url(SamGui/Assets/Textures/label_bg_toggle.png); } """)

        # build layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.class_toggle)
        self.layout.addWidget(self.delete_btn)
        self.setLayout(self.layout)

    def switch_label(self):
        if self.label_class == 1: # why does Python not store the "actual" enum value but the integers !?
            self.label_class = Label.background
            self.class_toggle.setToolTip("Toggle label to foreground")
            self.controller.update_anchor_class(self.guid, self.label_class)
        else:
            self.label_class = Label.foreground
            self.class_toggle.setToolTip("Toggle label to background")
            self.controller.update_anchor_class(self.guid, self.label_class)


class CanvasBBoxEntry(CanvasHierarchyEntry):
    def __init__(self, guid: UUID, controller: CanvasController, label: str = "BBox", parent=None):
        super().__init__(guid, controller, label, parent)
        self.edit_icon = QIcon("SamGui/Assets/Textures/edit_icon_light.png")
        self.edit_icon_hover = QIcon("SamGui/Assets/Textures/edit_icon_light_hover.png")
        self.edit_btn = MenuButton(self.edit_icon, self.edit_icon_hover, object_name="listButton")
        self.edit_btn.clicked.connect(self.edit_label)

        # build layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.edit_btn)
        self.layout.addWidget(self.delete_btn)
        self.setLayout(self.layout)

    def edit_label(self):
        dialog = TexInputDialog("Set new BBox name")
        dialog.exec()

        if dialog.edit_text.strip() != "":
            self.label.setText(dialog.edit_text)
            self.controller.update_bbox_label(self.guid, dialog.edit_text)