import os
import shutil

from PIL import Image
from uuid import UUID
from SamGui.Styles import DARK_STYLE
from SamGui.MVVM.viewmodel import SamViewModel
from SamGui.Controller import HeaderController
from SamGui.Utils import get_filename, generate_uuid, create_dir
from SamGui.Data import SegmentationData, Anchor, BBox, Mask, SAMMode, YoloAnnotations, SamResult, BatchSamResult, \
    CroppedExportData, MaskExportData, ProjectData, BBoxPosition, AnchorPosition, ErrorMessage
from SamGui.Widgets.Layout import Header, MainHierarchy, CanvasPanel
from SamGui.Widgets.Dialogs import SamDialog, NotificationWindow, SettingsWindow, ImportProjectDialog, \
    PickDirectoryDialog

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton, QLabel, \
    QTableWidget, QLineEdit, QTableWidgetItem


class DebugEntry(QWidget):
    def __init__(self):
        super().__init__()

class DebugView(QWidget):
    def __init__(self, title: str, guid: UUID, view_model: SamViewModel):
        super().__init__()
        self.title = title
        self.setObjectName("DebugView")
        self.view_model = view_model
        self.setMinimumWidth(760)
        self.setMinimumHeight(380)
        self.label = QLabel("Debug View")
        self.filter_label = QLineEdit()
        self.filter_label.setObjectName("DebugFilterLabel")
        self.data_table = QTableWidget()
        self.data_table.setObjectName("DebugDataTable")
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels(
            ["guid", "file name", "annotation type", "x", "y", "width", "height"]
        )


        self.btn_close = QPushButton("Close")
        self.btn_close.setObjectName("DialogButton")

        # bind signals
        self.btn_close.clicked.connect(self.close)
        self.view_model.s_dataSelected.connect(self.select_data)
        self.view_model.s_debugUpdate.connect(self.update_data)
        self.view_model.s_debugUpdateBBox.connect(self.update_bbox)
        self.view_model.s_debugUpdateAnchor.connect(self.update_anchor_position)
        self.view_model.s_debugUpdateBBoxData.connect(self.update_bbox_position)

        # build layout
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.label)
        self.v_layout.addWidget(self.filter_label)
        self.v_layout.addWidget(self.data_table)
        self.v_layout.addWidget(self.btn_close)
        self.setLayout(self.v_layout)

        self.setStyleSheet(DARK_STYLE)
        self.show()

        self.init_data(guid)

    def init_data(self, guid: UUID):
        current_data = self.view_model.get_data_by_guid(guid)
        print(f"DebugView -> init_data: {current_data}")

        if current_data is not None:
            self.select_data(current_data)

    def select_data(self, data: SegmentationData):
        next_row = 0

        if len(data.anchors) > 0:
            for _anchor in data.anchors:
                self.add_anchor(next_row, data.file_name, _anchor)
                next_row += 1

        if len(data.bboxes) > 0:
            for _bbox in data.bboxes:
                self.add_bbox(next_row, data.file_name, _bbox)
                next_row += 1


    def add_anchor(self, row_idx: int, file_name, anchor: Anchor):
        self.data_table.setItem(row_idx, 0, QTableWidgetItem(str(anchor.guid)))
        self.data_table.setItem(row_idx, 1, QTableWidgetItem(file_name))
        self.data_table.setItem(row_idx, 2, QTableWidgetItem("Anchor"))
        self.data_table.setItem(row_idx, 3, QTableWidgetItem(str(anchor.x)))
        self.data_table.setItem(row_idx, 4, QTableWidgetItem(str(anchor.y)))
        self.update()

    def add_bbox(self, row_idx: int, file_name: str, bbox: BBox):
        self.data_table.setItem(row_idx, 0, QTableWidgetItem(str(bbox.guid)))
        self.data_table.setItem(row_idx, 1, QTableWidgetItem(file_name))
        self.data_table.setItem(row_idx, 2, QTableWidgetItem(bbox.name))
        self.data_table.setItem(row_idx, 3, QTableWidgetItem(str(bbox.x)))
        self.data_table.setItem(row_idx, 4, QTableWidgetItem(str(bbox.y)))
        self.data_table.setItem(row_idx, 5, QTableWidgetItem(str(bbox.w)))
        self.data_table.setItem(row_idx, 6, QTableWidgetItem(str(bbox.h)))
        self.update()

    def update_data(self, project_data: ProjectData):
        item_count = 0
        self.data_table.clear()
        self.data_table.setHorizontalHeaderLabels(
            ["guid", "file name", "annotation type", "x", "y", "width", "height"]
        )

        for idx, data in project_data.data.items():
            item_count += 1
            anchor_cnt = len(data.anchors)
            bboxes_cnt = len(data.bboxes)
            item_count += anchor_cnt
            item_count += bboxes_cnt

        self.data_table.setRowCount(item_count)

        next_row = 0
        for guid, _d in project_data.data.items():
            file_n = _d.file_name
            _anchors = _d.anchors
            _bboxes = _d.bboxes

            if len(_anchors) > 0:
                for _anchor in _anchors:
                    self.add_anchor(next_row, file_n, _anchor)
                    next_row += 1

            if len(_bboxes) > 0:
                for _bbox in _bboxes:
                    self.add_bbox(next_row, file_n, _bbox)
                    next_row += 1


    def update_bbox(self, bbox: BBox):
        row_cnt = self.data_table.rowCount()
        guid_column = 0
        file_n_column = 1

        for row_idx in range(row_cnt):
            _guid_item = self.data_table.item(row_idx, guid_column)
            _file_n_item = self.data_table.item(row_idx, file_n_column)

            if _guid_item is not None and _file_n_item is not None:
                _guid = _guid_item.text()
                _file_n = _file_n_item.text()

                if _guid == bbox.guid:
                    self.add_bbox(row_idx, _file_n, bbox)
                    return

    def update_bbox_position(self, data: BBoxPosition):
        row_cnt = self.data_table.rowCount()
        guid_column = 0
        file_n_column = 1

        for row_idx in range(row_cnt):
            _guid_item = self.data_table.item(row_idx, guid_column)
            _file_n_item = self.data_table.item(row_idx, file_n_column)

            if _guid_item is not None and _file_n_item is not None:
                _guid = _guid_item.text()
                _file_n = _file_n_item.text()

                if _guid == str(data.guid):
                    self.data_table.item(row_idx, 3).setText(str(data.x))
                    self.data_table.item(row_idx, 4).setText(str(data.y))
                    self.data_table.item(row_idx, 5).setText(str(data.w))
                    self.data_table.item(row_idx, 6).setText(str(data.h))

    def update_anchor_position(self, data: AnchorPosition):
        row_cnt = self.data_table.rowCount()
        guid_column = 0
        file_n_column = 1

        for row_idx in range(row_cnt):
            _guid_item = self.data_table.item(row_idx, guid_column)
            _file_n_item = self.data_table.item(row_idx, file_n_column)

            if _guid_item is not None and _file_n_item is not None:
                _guid = _guid_item.text()
                _file_n = _file_n_item.text()

                if _guid == str(data.guid):
                    self.data_table.item(row_idx, 3).setText(str(data.x))
                    self.data_table.item(row_idx, 4).setText(str(data.y))

    def close_window(self):
        self.close()


class AppView(QWidget):
    def __init__(self, view_model: SamViewModel):
        super().__init__()
        self.view_model = view_model
        self.setObjectName("AppView")
        self.setWindowTitle("SamGui 1.0")
        self.debug_view = None
        self.threadpool = QThreadPool()
        # create controllers
        self.header_controller = HeaderController()
        self.sam_mode = SAMMode.bbox
        self.adjust_bbox = True
        self.current_guid = None

        # create main widgets
        self.header = Header(self.header_controller, parent=self)
        self.main_hierarchy = MainHierarchy(self.view_model)
        self.canvas_panel = CanvasPanel(
            self.view_model, self.header_controller, parent=self
        )

        # bind signals
        self.header_controller.s_new_project.connect(self.set_new_project)
        self.header_controller.s_import_images.connect(self.import_images)
        self.header_controller.s_import_project.connect(self.import_project)
        self.header_controller.s_export_project.connect(self.batch_export_yolo)
        self.header_controller.s_run_sam.connect(self.run_sam)
        self.header_controller.s_open_sam_settings.connect(self.show_sam_settings)
        self.header_controller.s_toggle_debug.connect(self.toggle_debug_view)

        self.view_model.s_dataSelected.connect(self.handle_data_selection)
        self.view_model.s_exportMasKData.connect(self.export_full_mask)
        self.view_model.s_exportCroppedData.connect(self.export_cropped_data)
        self.view_model.s_export_yolo_data.connect(self.export_annotations)
        self.view_model.s_error.connect(self.handle_error)

        # build layout
        self.main_layout = QVBoxLayout()
        self.right_panel = QVBoxLayout()
        self.right_panel.addWidget(self.main_hierarchy)

        self.content_layout = QHBoxLayout()
        self.main_layout.addWidget(self.header)
        self.content_layout.addLayout(self.right_panel)
        self.content_layout.addWidget(self.canvas_panel)

        self.main_layout.addLayout(self.content_layout)
        self.setLayout(self.main_layout)
        self.show()

        self.setStyleSheet(DARK_STYLE)

    def set_new_project(self):
        self.view_model.clear_project()
        self.canvas_panel.canvas_controller.clear_data()

    def handle_data_selection(self, data: SegmentationData):
        self.current_guid = data.guid

    def import_images(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        dialog.setViewMode(QFileDialog.ViewMode.List)

        if dialog.exec():
            file_paths = dialog.selectedFiles()
            segmentation_data = {}

            if file_paths is not None and len(file_paths) > 0:
                for file_path in file_paths:
                    guid = generate_uuid()
                    file_name = get_filename(file_path)
                    data = SegmentationData(
                        guid=guid,
                        file_path=file_path,
                        file_name=file_name,
                        x=0,
                        y=0,
                        anchors=[],
                        bboxes=[],
                        mask=Mask(
                            guid=generate_uuid(),
                            x=0,
                            y=0,
                            image=None
                        ),
                        zoom=1.0
                    )

                    segmentation_data[guid] = data

            self.view_model.add_data(segmentation_data)

    def import_project(self):
        import_dialog = ImportProjectDialog(self.view_model)
        import_dialog.exec()

        images = import_dialog.images
        labels = import_dialog.labels
        classes = import_dialog.classes

        self.view_model.import_yolo_data(images, labels, classes)


    def toggle_debug_view(self):
        self.debug_view = DebugView("Debug View", self.current_guid, self.view_model)

    def show_sam_settings(self):
        dialog = SettingsWindow(self.sam_mode, self.adjust_bbox)

        if dialog.exec():
            self.sam_mode = dialog.current_mode
            self.adjust_bbox = dialog.adjust_bbox

    def run_sam(self):
        project_data = self.view_model.get_data()
        current_image_guid = self.canvas_panel.current_image_guid

        if current_image_guid is None or project_data.data is None or len(project_data.data) == 0:
            dialog = NotificationWindow("Project is empty", "The Project contains no data to run SAM on.")
            dialog.exec()
            return

        _data = project_data.data[current_image_guid]

        if len(_data.anchors) == 0 and len(_data.bboxes) == 0:
            dialog = NotificationWindow("No Annotations", "The Project has no annotations.")
            dialog.exec()
            return

        elif self.sam_mode == SAMMode.anchors and len(_data.anchors) == 0:
            notification = NotificationWindow("Invalid Sam Mode", "You selected Anchor Mode for the SAM model, but there weren't placed any anchors.")
            notification.exec()
            return

        elif self.sam_mode == SAMMode.bbox and len(_data.bboxes) == 0:
            notification = NotificationWindow("Invalid Sam Mode", "You selected BBox Mode for the SAM model, but there weren't placed any BBoxes.")
            notification.exec()
            return

        else:
            dialog = SamDialog(_data, self.sam_mode, self.adjust_bbox, self.threadpool, self)
            dialog.sign_result.connect(self.save_generated_mask)
            dialog.sign_sam_result.connect(self.handle_sam_result)
            dialog.sign_batch_result.connect(self.handle_sam_batch_result)
            dialog.s_error.connect(self.handle_error)
            dialog.exec()


    """
    There is an inconsistency in handling the SAM Results, save_generated_masks is called when SAM is run in Anchor-mode
    
    """
    def handle_sam_result(self, result: SamResult):
        self.view_model.update_sam_result(result)

    def handle_sam_batch_result(self, result: BatchSamResult):
        self.view_model.update_sam_batch_result(result)

    def save_generated_mask(self, result: Image.Image):
        current_image_guid = self.canvas_panel.current_image_guid
        if current_image_guid is not None:
            self.view_model.add_mask(current_image_guid, result)

    def export_full_mask(self, data:  MaskExportData):
        if data is not None:
            dialog = PickDirectoryDialog("Select Save Directory...")
            dir_path = dialog.getExistingDirectory(self)

            if dir_path is not None and os.path.isdir(dir_path):
                for idx, mask in enumerate(data.masks):
                    out_img = f"{dir_path}/{data.file_name}_{idx}_mask.jpg"
                    mask.save(out_img)

    def export_cropped_data(self, data: CroppedExportData):
        if data is not None:
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setViewMode(QFileDialog.ViewMode.List)
            dir_path = dialog.getExistingDirectory(self)

            if dir_path is not None and os.path.isdir(dir_path):

                for idx, (image, mask) in enumerate(zip(data.images, data.masks)):
                    out_img = f"{dir_path}/{data.file_name}_{idx}.jpg"
                    image.save(out_img)

                    out_img = f"{dir_path}/{data.file_name}_{idx}_mask.jpg"
                    mask.save(out_img)
        else:
            dialog = NotificationWindow(
                "No BBoxes found",
                "No BBoxes are associated with this mask, "
                "so you might want to add at least one.")
            dialog.exec()

    # used for individual annotations when selected from the ImportedImages list
    def export_annotations(self, annotations: YoloAnnotations):
        dialog = PickDirectoryDialog
        dir_path = dialog.getExistingDirectory(self)

        if dir_path is not None and os.path.isdir(dir_path):
            annotations_out_file = f"{dir_path}/{annotations.file_name}.txt"
            classes_out_file = f"{dir_path}/classes.txt"

            with open(classes_out_file, "w+", encoding="utf-8") as f:
                for class_name in annotations.classes:
                    f.write(f"{class_name}\n")

            with open(annotations_out_file, "w+", encoding="utf-8") as f:
                for annotation in annotations.annotations:
                    f.write(f"{annotation.class_id} {annotation.center_x} {annotation.center_y} {annotation.width} {annotation.height}\n")

    # batch export for every image in the project
    def batch_export_yolo(self):
        all_annotations, image_paths, project_classes = self.view_model.batch_export_project_annotations()

        if len(all_annotations) > 0:
            dialog = PickDirectoryDialog("Set Save Directory...")
            dir_path = dialog.getExistingDirectory(self)
            annotations_dir = os.path.join(dir_path, "annotations")
            images_dir = os.path.join(dir_path, "images")

            create_dir(images_dir)
            create_dir(annotations_dir)

            if dir_path is not None and os.path.isdir(dir_path):
                for yolo_annotations, image_path in zip(all_annotations, image_paths):
                    annotations_out_file = f"{annotations_dir}/{yolo_annotations.file_name}.txt"

                    with open(annotations_out_file, "w+", encoding="utf-8") as f:
                        for yolo_a in yolo_annotations.annotations:
                            f.write(
                                f"{yolo_a.class_id} {yolo_a.center_x} {yolo_a.center_y} {yolo_a.width} {yolo_a.height}\n")

                    img_name = get_filename(image_path)
                    ext = os.path.splitext(image_path)[1]
                    target_img = f"{images_dir}/{img_name}{ext}"
                    shutil.copy(image_path, target_img)

                classes_out_file = f"{dir_path}/classes.txt"

                with open(classes_out_file, "w+", encoding="utf-8") as f:
                    for class_name in project_classes:
                        f.write(f"{class_name}\n")

        else:
            dialog = NotificationWindow(
                "No BBoxes found",
                "There aren't any BBoxes in the Project. To export YOLO annotations, you have to place BBoxes first.")
            dialog.exec()

    def handle_error(self, error: ErrorMessage):
        dialog = NotificationWindow(
            error.type,
            error.message)
        dialog.exec()