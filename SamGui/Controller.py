from uuid import UUID
from PySide6.QtCore import QObject, Signal
from SamGui.Data import Tool, Label, Anchor, AnchorState, BBox, BBoxState, BBoxLabel, \
    SamResult, BatchSamResult, ZoomLevel, BBoxPosition, ErrorMessage


class WorkerSignals(QObject):
    s_finished = Signal()  # QtCore.Signal
    s_error = Signal(ErrorMessage)
    s_sam_result = Signal(SamResult)
    s_sam_batch_result = Signal(BatchSamResult)

class HeaderController(QObject):
    s_new_project = Signal()
    s_import_images = Signal()
    s_import_project = Signal()
    s_export_project = Signal()
    s_import_annotations = Signal()
    s_save_annotations = Signal()
    s_clear_canvas = Signal()
    s_export_masks = Signal()
    s_current_tool = Signal(Tool)
    s_select_tool = Signal(Tool)
    s_toggle_debug = Signal()
    s_run_sam = Signal()
    s_open_sam_settings = Signal()

    def __init__(self):
        super().__init__()

    def set_new_project(self):
        self.s_new_project.emit()

    def import_images(self):
        self.s_import_images.emit()

    def import_project(self):
        self.s_import_project.emit()

    def import_annotations(self):
        self.s_import_annotations.emit()

    def save_annotations(self):
        self.s_save_annotations.emit()

    def export_project(self):
        self.s_export_project.emit()

    def export_masks(self):
        self.s_export_masks.emit()

    def set_tool(self, tool: Tool):
        self.s_select_tool.emit(tool)

    def clear_canvas(self):
        self.s_clear_canvas.emit()

    def toggle_debug(self):
        self.s_toggle_debug.emit()

    def run_sam(self):
        self.s_run_sam.emit()

    def open_settings(self):
        self.s_open_sam_settings.emit()


class CanvasController(QObject):
    s_clear_data = Signal()
    s_toggle_anchor_state = Signal(AnchorState)
    s_toggle_bbox_state = Signal(BBoxState)
    s_delete_element = Signal(UUID)
    s_delete_elements = Signal()
    s_add_anchor = Signal(Anchor)
    s_add_bbox = Signal(BBox)
    s_select_canvas_item = Signal(UUID)
    s_update_anchor_position = Signal(Anchor)
    s_update_bbox_position = Signal(BBoxPosition)
    s_update_anchor_class = Signal(tuple)  # [UUID, Label]
    s_update_bbox_label = Signal(BBoxLabel)
    s_update_zoom = Signal(ZoomLevel)

    def __init__(self):
        super().__init__()

    def add_canvas_anchor(self, anchor: Anchor):
        self.s_add_anchor.emit(anchor)

    def add_canvas_bbox(self, bbox: BBox):
        self.s_add_bbox.emit(bbox)

    def toggle_anchor_state(self, guid: UUID, active: bool):
        state = AnchorState(guid, active)
        self.s_toggle_anchor_state.emit(state)

    def toggle_bbox_state(self, guid: UUID, active: bool):
        state = BBoxState(guid, active)
        self.s_toggle_bbox_state.emit(state)

    def delete_canvas_annotation(self, guid: UUID):
        self.s_delete_element.emit(guid)

    def delete_all_canvas_annotations(self):
        self.s_delete_elements.emit()

    def update_anchor_class(self, guid: UUID, label: Label):
        self.s_update_anchor_class.emit([guid, label]) # Does passing a Tuple work reliably?

    def update_bbox_label(self, guid: UUID, label: str):
        bbox_label = BBoxLabel(guid, label)
        self.s_update_bbox_label.emit(bbox_label)

    def select_item(self, guid: UUID):
        self.s_select_canvas_item.emit(guid)

    def clear_data(self):
        self.s_clear_data.emit()

    def update_zoom(self, guid: UUID, zoom_factor: float):
        zoom_level = ZoomLevel(guid, zoom_factor)
        self.s_update_zoom.emit(zoom_level)