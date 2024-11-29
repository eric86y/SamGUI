import os.path
from PIL import Image
from glob import glob
from natsort import natsorted
from SamGui.MVVM.viewmodel import SamViewModel
from SamGui.Widgets.Buttons import DialogButton
from SamGui.Utils import get_file_extension, get_filename, read_class_file
from SamGui.Data import SAMMode, SegmentationData, SamResult, BatchSamResult, ErrorMessage
from SamGui.Runners import SAMRunner
from PySide6.QtCore import Qt, Signal, QThreadPool
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QMessageBox, QVBoxLayout, QRadioButton, QLabel, QDialogButtonBox,
                               QFileDialog, QPushButton, QCheckBox, QInputDialog, QLineEdit,
                               QProgressBar)

from SamGui.Styles import DARK_STYLE


class NotificationWindow(QMessageBox):
    def __init__(self, title: str, message: str):
        super().__init__()
        self.setObjectName("NotificationWindow")
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(440)
        self.setIcon(QMessageBox.Icon.Information)
        self.setText(message)

        self.ok_btn = QPushButton("Ok")
        self.ok_btn.setObjectName("DialogButton")

        self.addButton(self.ok_btn, QMessageBox.ButtonRole.YesRole)
        self.setStyleSheet(DARK_STYLE)


class ConfirmationWindow(QMessageBox):
    def __init__(self, title: str, message: str, show_cancel: bool = True):
        super().__init__()
        self.setObjectName("NotificationWindow")
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(440)
        self.setIcon(QMessageBox.Icon.Information)
        self.setText(message)

        self.ok_btn = QPushButton("Ok")
        self.ok_btn.setObjectName("DialogButton")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DialogButton")

        if show_cancel:
            self.addButton(self.ok_btn, QMessageBox.ButtonRole.YesRole)
            self.addButton(self.cancel_btn, QMessageBox.ButtonRole.NoRole)
        else:
            self.addButton(self.ok_btn, QMessageBox.ButtonRole.YesRole)

        self.setStyleSheet(DARK_STYLE)

class InputDialog(QInputDialog):
    def __init__(self, label: str):
        super().__init__()
        print(f"Creating Custom InputDialog")
        self.setFixedWidth(400)
        self.setFixedHeight(400)
        self.setLabelText(label)


class TexInputDialog(QDialog):
    def __init__(self, title: str):
        super(TexInputDialog, self).__init__()
        self.title = title
        self.edit_text = ""
        self.setFixedWidth(280)
        self.setWindowTitle(title)
        self.spacer = QLabel()
        self.spacer.setFixedHeight(12)
        self.line_edit = QLineEdit(self)
        self.line_edit.textEdited.connect(self.update_text)
        self.line_edit.setStyleSheet("""
            color: #ffffff;
            background-color: #3e5272;
            border: 2px solid #3e5272;
            border-radius: 8px;
            padding: 4px;

        """)

        self.accept_btn = DialogButton("Accept")
        self.reject_btn = DialogButton("Reject")

        self.accept_btn.clicked.connect(self.accept_change)
        self.reject_btn.clicked.connect(self.reject_change)

        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.accept_btn)
        self.h_layout.addWidget(self.reject_btn)

        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.line_edit)
        self.v_layout.addWidget(self.spacer)
        self.v_layout.addLayout(self.h_layout)

        self.setLayout(self.v_layout)
        self.setStyleSheet("""
            background-color: #08091e;
        """)

    def update_text(self, value: str):
        self.edit_text = value

    def accept_change(self):
        self.accept()

    def reject_change(self):
        self.reject()


class SettingsWindow(QDialog):
    def __init__(self, current_mode: SAMMode, adjust_bbox: bool):
        super().__init__()
        self.setWindowTitle("Sam Settings")
        self.current_mode = current_mode
        self.adjust_bbox = adjust_bbox
        self.setFixedHeight(300)
        self.setFixedWidth(600)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.label = QLabel("Sam Settings")
        self.spacer = QLabel()
        self.label.setFixedHeight(32)

        self.btn_anchor_mode = QRadioButton("Anchor Mode")
        self.btn_bbox_mode = QRadioButton("BBox Mode")
        self.btn_adjust_bbox = QCheckBox("Adjust BBox by SAM")
        self.btn_adjust_bbox.setChecked(self.adjust_bbox)

        # bind signals
        self.btn_anchor_mode.clicked.connect(self.set_anchor_mode)
        self.btn_bbox_mode.clicked.connect(self.set_bbox_mode)
        self.btn_adjust_bbox.clicked.connect(self.toggle_bbox_check)

        # define layout
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.label)
        self.v_layout.addWidget(self.btn_anchor_mode)
        self.v_layout.addWidget(self.btn_bbox_mode)
        self.v_layout.addWidget(self.spacer)
        self.v_layout.addWidget(self.btn_adjust_bbox)

        self.h_layout = QHBoxLayout()
        self.default_buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(self.default_buttons)

        self.buttonBox.setStyleSheet("""
            width: 240px;
            height: 32px;
            color: #000000;
            font: bold 14px;
            border: 2px solid #ffad00;
            background-color: #ffad00;
            border-radius: 4px;
        
        """)

        self.label.setStyleSheet("""
            QLabel {
                padding-left: 4px;
                font: bold 12px;
                background-color: #ffad00;
                border: 2px solid #ffad00;
                border-radius: 4px;
            }
        """)

        self.btn_anchor_mode.setStyleSheet("""
            color: #ffffff;
            padding-top: 6px;
            padding-bottom: 6px;
            background-color: #1e1a3d;
            border: 4px solid #1e1a3d;
            border-radius: 4px;
        
        """)

        self.btn_bbox_mode.setStyleSheet("""
           color: #ffffff;
           padding-top: 6px;
           padding-bottom: 6px;
           background-color: #1e1a3d;
           border: 4px solid #1e1a3d;
           border-radius: 4px;
        """)


        self.btn_adjust_bbox.setStyleSheet("""
            color: #ffffff;
        """)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.h_layout.addWidget(self.buttonBox)

        self.v_layout.addLayout(self.h_layout)
        self.setLayout(self.v_layout)

        if self.current_mode == SAMMode.anchors:
            self.btn_anchor_mode.setChecked(True)
        elif self.current_mode == SAMMode.bbox:
            self.btn_bbox_mode.setChecked(True)

        self.setStyleSheet("""
            background-color: #24272c;
        """)

    def set_anchor_mode(self):
        self.current_mode = SAMMode.anchors
        self.btn_anchor_mode.setChecked(True)

    def set_bbox_mode(self):
        self.current_mode = SAMMode.bbox
        self.btn_bbox_mode.setChecked(True)


    def toggle_bbox_check(self):
        print(f"Toogle BBox Check: {self.btn_adjust_bbox.isChecked()}")
        self.adjust_bbox = self.btn_adjust_bbox.isChecked()


class IODialog(QFileDialog):
    def __init__(self, view_mode: QFileDialog.ViewMode, file_mode: QFileDialog.FileMode, parent=None):
        super().__init__()
        self.view_mode = view_mode
        self.file_mode = file_mode

class SaveFileDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super(SaveFileDialog, self).__init__(parent)
        self.title = title
        self.view_mode = QFileDialog.ViewMode.List
        self.file_mode = QFileDialog.FileMode.AnyFile
        self.setWindowTitle(self.title)

class PickDirectoryDialog(QFileDialog):
    def __init__(self, title: str = "Set Directory", parent=None):
        super(PickDirectoryDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.setFileMode(QFileDialog.FileMode.Directory)


class ImportProjectDialog(QDialog):
    def __init__(self, view_model: SamViewModel, parent=None):
        super(ImportProjectDialog, self).__init__(parent)
        self.setObjectName("ImportDialog")
        self.setWindowTitle("Import Project")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.view_model = view_model
        self.current_class_file = ""
        self.current_import_dir = ""
        self.images = []
        self.labels = []
        self.classes = []

        self.label = QLabel("Import Yolo Dataset")
        self.label.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        """)

        self.spacer = QLabel()
        self.spacer.setFixedHeight(16)
        self.label.setFixedHeight(32)

        self.classes_file_path = QLineEdit()
        self.classes_file_path.setObjectName("DialogLineEdit")
        self.classes_file_path.setText("")
        self.classes_file_path.setStyleSheet("""
            color: #ffffff;
            background-color: #3e5272;
            border: 2px solid #3e5272;
            border-radius: 8px;
            padding: 4px;
        """)


        self.import_dir_path = QLineEdit()
        self.import_dir_path.setObjectName("DialogLineEdit")
        self.import_dir_path.setText("")
        self.import_dir_path.setStyleSheet("""
                    color: #ffffff;
                    background-color: #3e5272;
                    border: 2px solid #3e5272;
                    border-radius: 8px;
                    padding: 4px;
                """)

        self.btn_select_class_file = DialogButton("Select Classes file")
        self.btn_select_import_dir = DialogButton("Select Data Directory")

        self.default_buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(self.default_buttons)

        self.buttonBox.setStyleSheet("""
                    width: 240px;
                    height: 32px;
                    color: #000000;
                    font: bold 14px;
                    border: 2px solid #ffad00;
                    background-color: #ffad00;
                    border-radius: 4px;
                """)

        # connect signals
        self.btn_select_class_file.clicked.connect(self.select_classes_file)
        self.btn_select_import_dir.clicked.connect(self.select_import_dir)

        self.buttonBox.accepted.connect(self.run_import)
        self.buttonBox.rejected.connect(self.cancel)

        # build layout
        self.h_layout_import_file = QHBoxLayout()
        self.h_layout_import_file.addWidget(self.classes_file_path)
        self.h_layout_import_file.addWidget(self.btn_select_class_file)

        self.h_layout_save_dir = QHBoxLayout()
        self.h_layout_save_dir.addWidget(self.import_dir_path)
        self.h_layout_save_dir.addWidget(self.btn_select_import_dir)

        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.label)
        self.v_layout.addWidget(self.spacer)
        self.v_layout.addLayout(self.h_layout_import_file)
        self.v_layout.addLayout(self.h_layout_save_dir)
        self.v_layout.addWidget(self.spacer)

        self.v_layout.addWidget(self.buttonBox)
        self.setLayout(self.v_layout)
        self.setStyleSheet(DARK_STYLE)

    def run_import(self):
        if os.path.exists(self.current_import_dir) and os.path.isfile(self.current_class_file):
            try:
                self.classes = read_class_file(self.current_class_file)

                _image_dir = os.path.join(self.current_import_dir, "images")
                _labels_dir = os.path.join(self.current_import_dir, "annotations")

                if not os.path.isdir(_image_dir) or not os.path.isdir(_labels_dir):
                    info = NotificationWindow(
                        "Invalid Directory structure",
                        "The selected directory has an invalid folder structure. Images need to be in /images, labels in /labels"
                        )

                    info.exec()
                else:
                    self.images = natsorted(glob(f"{self.current_import_dir}/images/*"))
                    self.labels = natsorted(glob(f"{self.current_import_dir}/annotations/*.txt"))

                    if len(self.images) != len(self.labels):
                        info = NotificationWindow(
                            "Images and Labels don't match",
                            "The number if images and labels don't match."
                        )
                        info.exec()

                    self.accept()


            except BaseException as e:
                info = NotificationWindow(
                    "Error importing dataset",
                    f"The dataset from {get_filename(self.current_import_dir)} could not be imported: {e}.")
                info.exec()

    def cancel(self):
        self.reject()

    def select_classes_file(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.List)
        dialog.setNameFilter("*.txt")
        dialog.setViewMode(QFileDialog.ViewMode.List)

        classes_file = dialog.getOpenFileName() # returns a Tuple[file_path, fiter)
        classes_file_name, _ = classes_file
        extension = get_file_extension(classes_file_name)

        if classes_file is not None and extension == "txt":
            self.classes_file_path.setText(classes_file_name)
            self.current_class_file = classes_file_name


    def select_import_dir(self):
        target_dialog = PickDirectoryDialog("Select import directory")
        dir_path = target_dialog.getExistingDirectory(self)

        if dir_path is not None and dir_path != "" and os.path.isdir(dir_path):
            self.import_dir_path.setText(dir_path)
            self.current_import_dir = dir_path
        else:
            notification = NotificationWindow("No Valid Directory selected",
                                              "No valid directory was selected. Please select a valid directory for saving the imported images.")
            notification.exec()


class SamDialog(QDialog):
    sign_result = Signal(Image.Image)
    sign_sam_result = Signal(SamResult)
    sign_batch_result = Signal(BatchSamResult)
    s_error = Signal(ErrorMessage)

    def __init__(self, data: SegmentationData, mode: SAMMode, adjust_bbox: bool, pool: QThreadPool, parent=None):
        super(SamDialog, self).__init__(parent)
        self.setObjectName("SamDialog")
        self.setFixedWidth(360)
        self.setFixedHeight(140)
        self.setWindowTitle("SAM Mask Generation")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.encoder_path: str = "SamGui/Models/sam_vit_b_encoder.onnx"
        self.decoder_path: str = "SamGui/Models/sam_vit_b_decoder.onnx"

        self.data = data
        self.mode = mode
        self.pool = pool
        self.adjust_bbox = adjust_bbox
        self.label = QLabel("Running Mask Generation....")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(360)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)

        self.button_h_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Ok")
        self.ok_btn.setObjectName("DialogButton")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DialogButton")

        self.button_h_layout.addWidget(self.ok_btn)
        self.button_h_layout.addWidget(self.cancel_btn)

        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(self.label)
        self.v_layout.addWidget(self.progress_bar)
        self.v_layout.addLayout(self.button_h_layout)
        self.setLayout(self.v_layout)

        # bind signals
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        self.show()

    def exec(self):
 
        if not os.path.isfile(self.encoder_path):
            error_msg = ErrorMessage("Encoder not Found", "The model encoder was not found. Make sure you have sam_vit_b_encoder.onnx in your SamGui/Models directory.")
            self.s_error.emit(error_msg)
            self.close()
            return
        
        if not os.path.isfile(self.encoder_path):
            error_msg = ErrorMessage("Decoder not Found", "The model encoder was not found. Make sure you have sam_vit_b_decoder.onnx in your SamGui/Models directory.")
            self.s_error.emit(error_msg)
            self.close()
            return

        worker = SAMRunner(self.data, self.mode, self.adjust_bbox, encoder_path=self.encoder_path, decoder_path=self.decoder_path)
        worker.signals.s_sam_result.connect(self.handle_sam_result)
        worker.signals.s_sam_batch_result.connect(self.handle_sam_batch_result)
        worker.signals.s_finished.connect(self.thread_complete)
        worker.signals.s_error.connect(self.handle_error)
        self.pool.start(worker)

    def handle_sam_result(self, result: SamResult):
        self.sign_sam_result.emit(result)

    def handle_sam_batch_result(self, result: BatchSamResult):

        self.sign_batch_result.emit(result)

    def handle_empty_result(self, result: Image.Image):
        self.sign_result.emit(result)

    def handle_error(self, error: ErrorMessage):
        print(f"SamDialog -> Handling Error: {error}")
        self.s_error.emit(error)
        self.close()

    def thread_complete(self):
        self.close()
