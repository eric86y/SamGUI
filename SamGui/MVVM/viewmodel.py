from uuid import UUID
from PIL import Image
from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Tuple
from SamGui.MVVM.model import DataModel
from SamGui.Utils import create_crop_image, generate_uuid, get_filename
from SamGui.Data import (
    Mask,
    SegmentationData,
    Anchor,
    BBox,
    BBoxPosition,
    BBoxState,
    AnchorPosition,
    ProjectData,
    YoloAnnotation,
    YoloAnnotations, SamResult, BatchSamResult, ZoomLevel, MaskExportData, CroppedExportData, ImagePosition,
    MaskPosition, ErrorMessage
)


class SamViewModel(QObject):
    s_dataAdded = Signal(ProjectData)
    s_dataChanged = Signal(ProjectData)
    s_dataSelected = Signal(SegmentationData)
    s_dataRemoved = Signal(SegmentationData)
    s_dataCleared = Signal()
    s_maskSelected = Signal(Mask)
    s_exportMasKData = Signal(MaskExportData)
    s_exportCroppedData = Signal(CroppedExportData)
    s_export_yolo_data = Signal(YoloAnnotations)

    s_debugUpdate = Signal(ProjectData)
    s_debugUpdateAnchor = Signal(Anchor)
    s_debugUpdateBBox = Signal(BBox)
    s_debugUpdateAnchorPosition = Signal(AnchorPosition)
    s_debugUpdateBBoxData = Signal(BBoxPosition)
    s_error = Signal(ErrorMessage)

    def __init__(self, model: DataModel):
        super().__init__()
        self.model = model

    def clear_project(self):
        self.model.flush()
        self.s_dataChanged.emit(self.model.get_data())

    def add_data(self, data: Dict[UUID, SegmentationData]):
        self.model.add(data)
        # TODO: check again the difference between dataAdded and dataChanged events, maybe one is enough
        self.s_dataAdded.emit(self.model.project)
        self.s_dataChanged.emit(self.model.project)

    def import_data(self, data: Dict[UUID, SegmentationData], classes: List[str]):
        self.model.add(data)
        self.model.set_classes(classes)
        # TODO: check again the difference between dataAdded and dataChanged events, maybe one is enough
        self.s_dataAdded.emit(self.model.project)
        self.s_dataChanged.emit(self.model.project)

    def delete_item_by_guid(self, guid: UUID):
        self.model.delete_item(guid)
        self.s_dataChanged.emit(self.model.project)

    def select_data_by_guid(self, guid: UUID):
        self.s_dataSelected.emit(guid)

    def select_image_by_guid(self, guid: UUID):
        data = self.model.get_data_by_guid(guid)

        if data is not None:
            self.s_dataSelected.emit(data)

    def add_mask(self, image_guid: UUID, mask: Image.Image):
        self.model.add_mask_data(image_guid, mask)
        self.s_dataChanged.emit(self.model.project)

    def add_anchor(self, image_guid: UUID, anchor: Anchor):
        self.model.add_anchor(image_guid, anchor)
        self.s_debugUpdate.emit(self.model.project)

    def add_bbox(self, image_guid: UUID, bbox: BBox):
        self.model.add_bbox(image_guid, bbox)
        self.s_debugUpdate.emit(self.model.project)

    def remove_bbox(self, image_guid: UUID, bbox: BBox):
        self.model.remove_bbox(image_guid, bbox)

    def update_image_position(self, position: ImagePosition):
        self.model.update_image_position(position)

    def update_mask_position(self, data: MaskPosition):
        self.model.update_mask_position(data)

    def update_bbox_state(self, mask_guid: UUID, state: BBoxState):
        self.model.update_bbox_state(mask_guid, state)
        self.s_dataChanged.emit(self.model.project)

    def update_bbox_label(self, image_guid: UUID, bbox_guid: UUID, label: str):
        self.model.update_bbox_label(image_guid, bbox_guid, label)
        #self.s_dataChanged.emit(self.model.project)
        self.s_debugUpdate.emit(self.model.project)

    def update_anchor_position(self, image_guid: UUID, position: AnchorPosition):
        self.model.update_anchor_position(image_guid, position)
        self.s_debugUpdateAnchor.emit(position)

    def update_bbox_position(self, image_guid: UUID, position: BBoxPosition):
        self.model.update_bbox_position(image_guid, position)
        self.s_debugUpdateBBoxData.emit(position)

    def update_sam_result(self, result: SamResult):
        self.model.update_sam_result(result)
        self.s_dataChanged.emit(self.model.project)

    def update_sam_batch_result(self, result: BatchSamResult):
        self.model.update_sam_batch_result(result)
        self.s_dataChanged.emit(self.model.project)

    def update_zoom_level(self, zoom_level: ZoomLevel):
        self.model.update_zoom_level(zoom_level)

    def get_data(self) -> ProjectData:
        return self.model.get_data()

    def get_data_by_guid(self, guid: UUID):
        return self.model.get_data_by_guid(guid)

    def delete_images(self):
        self.model.delete_all_images()
        self.s_dataChanged.emit(self.model.get_data())

    def delete_annotations(self, image_guid: UUID):
        self.model.delete_annotations(image_guid)
        self.s_dataChanged.emit(self.model.get_data())

    def build_yolo_annotations(self, data: SegmentationData) -> YoloAnnotations | None:
        if len(data.bboxes) > 0:
            _yolo_annotations = []
            project_classes = self.model.project.classes
            image = Image.open(data.file_path).convert("RGB")
            width, height = image.size

            for bbox in data.bboxes:
                if bbox.name not in project_classes:
                    class_id = 999
                else:
                    class_id = project_classes.index(bbox.name)

                x_center = bbox.x + (bbox.w / 2)
                y_center = bbox.y + (bbox.h / 2)

                # Normalize values to the range [0, 1]
                x_center_norm = x_center / width
                y_center_norm = y_center / height
                width_norm = bbox.w / width
                height_norm = bbox.h / height

                yolo_annotation = YoloAnnotation(
                    class_id,
                    x_center_norm,
                    y_center_norm,
                    width_norm,
                    height_norm
                )
                print(f"Incoming BBox => x: {bbox.x}, y: {bbox.y}, w: {bbox.w}, h: {bbox.h}")
                print(f"Exporting Yolo annotation => x_center: {yolo_annotation.center_x}, y_center: {yolo_annotation.center_y}, bbox_w: {yolo_annotation.width}, bbox_h: {yolo_annotation.height}")

                _yolo_annotations.append(yolo_annotation)

            yolo_annotations = YoloAnnotations(
                file_name=data.file_name,
                classes=project_classes,
                annotations=_yolo_annotations
            )
            return yolo_annotations

        return None

    def import_yolo_data(self, images: List[str], labels: List[str], classes: List[str]):
        segmentation_data = {}

        for _image, _label in zip(images, labels):
            guid = generate_uuid()
            file_name = get_filename(_image)

            try:
                image = Image.open(_image).convert("RGB")

            except IOError as e:
                print(f"Import Error: {e}")
                continue

            width, height = image.size
            _bboxes = []

            with open(_label, "r") as f:
                _label_data = f.readlines()

                for _lbl in _label_data:
                    class_idx, yolo_center_x, yolo_center_y, yolo_bbox_w, yolo_bbox_h = _lbl.split(" ")

                    if len(classes) == 0:
                        class_name = "BBox"

                    elif class_idx == "999":
                        class_name = "BBox"

                    else:
                        class_name = classes[int(class_idx)]

                    bbox_width = float(yolo_bbox_w) * width
                    bbox_height = float(yolo_bbox_h) * height
                    x_center = float(yolo_center_x) * width
                    y_center = float(yolo_center_y) * height

                    x = x_center - (bbox_width / 2)
                    y = y_center - (bbox_height / 2)

                    bbox = BBox(
                        guid=generate_uuid(),
                        name=class_name,
                        active=True,
                        x = x,
                        y = y,
                        w = bbox_width,
                        h = bbox_height,
                    )

                    _bboxes.append(bbox)

            data = SegmentationData(
                guid=guid,
                file_path=_image,
                file_name=file_name,
                x=0,
                y=0,
                anchors=[],
                bboxes=_bboxes,
                mask=Mask(
                    guid=generate_uuid(),
                    x=0,
                    y=0,
                    image=None
                ),
                zoom=1.0
            )

            segmentation_data[guid] = data
        self.import_data(segmentation_data, classes)

    def export_yolo_annotations(self, image_guid: UUID):
        data = self.model.get_data()
        segmentation_data = data.data[image_guid]
        yolo_annotations = self.build_yolo_annotations(segmentation_data)

        if yolo_annotations is not None:
            self.s_export_yolo_data.emit(yolo_annotations)

        else:
            error_msg = ErrorMessage(
                "No BBOX annotations",
                "The project contains no BBox information that could be exported in YOLO format."
            )
            self.s_error.emit(error_msg)

    def export_mask(self, image_guid: UUID):
        project_data = self.model.get_data()
        segmentation_data = project_data.data[image_guid]
        mask_data = segmentation_data.mask

        if mask_data is not None and mask_data.image is not None:
            mask_image = mask_data.image
            export_data = MaskExportData(
                file_name=segmentation_data.file_name,
                masks=[mask_image]
            )
            self.s_exportMasKData.emit(export_data)

    def batch_export_project_annotations(self) -> Tuple[List[YoloAnnotations], List[str], List[str]]:
        project_data = self.model.get_data()
        all_annotations = []
        image_paths = []

        for guid, data in project_data.data.items():
            yolo_annotations = self.build_yolo_annotations(data)

            if yolo_annotations is not None:
                all_annotations.append(yolo_annotations)
                image_path = data.file_path
                image_paths.append(image_path)

        return all_annotations, image_paths, project_data.classes

    def export_masks_cropped(self, image_guid: UUID):
        project_data = self.model.get_data()
        segmentation_data = project_data.data[image_guid]

        mask_data = segmentation_data.mask
        image_path = segmentation_data.file_path
        image = Image.open(image_path)

        if mask_data is not None and mask_data.image is not None and image_path is not None:
            if len(segmentation_data.bboxes) > 0:
                crop_imgs = []
                crop_masks = []

                for bbox in segmentation_data.bboxes:
                    x_pos = segmentation_data.x
                    y_pos = segmentation_data.y

                    crop_img = create_crop_image(image, bbox, x_pos, y_pos)
                    crop_mask = create_crop_image(mask_data.image, bbox, x_pos, y_pos)
                    crop_imgs.append(crop_img)
                    crop_masks.append(crop_mask)

                assert(len(crop_imgs) == len(crop_masks))

                export_data = CroppedExportData(
                    file_name=segmentation_data.file_name,
                    images=crop_imgs,
                    masks=crop_masks)

                self.s_exportCroppedData.emit(export_data)
            else:
                error_msg = ErrorMessage(
                    "No BBOX annotations",
                    "The project contains no BBox information that could be exported in YOLO format."
                )
                self.s_error.emit(error_msg)
        else:
            error_msg = ErrorMessage(
                "No Mask",
                "The project contains no Mask, you need to generate a mask first."
            )
            self.s_error.emit(error_msg)

