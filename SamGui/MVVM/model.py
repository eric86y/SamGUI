from uuid import UUID
from PIL import Image
from typing import Dict, List
from SamGui.Utils import generate_uuid
from SamGui.Data import Anchor, BBox, Mask, SegmentationData, ProjectData, BBoxState, SamResult, \
    BatchSamResult, ZoomLevel, BBoxPosition, AnchorPosition, ImagePosition, MaskPosition


class DataModel:
    def __init__(self):
        self.project = ProjectData(
            guid=generate_uuid(),
            name="Default Segmentation Project",
            classes=[],
            data={}
        )

    def flush(self) -> None:
        self.project = ProjectData(
            guid=generate_uuid(),
            name="Default Segmentation Project",
            classes=[],
            data={}
        )

    def image_exists(self, file_path: str) -> bool:
        for k, seg_data in self.project.data.items():
            if seg_data.file_path == file_path:
                return True
        return False

    def get_data(self):
        return self.project

    def add_item(self, data: Dict[UUID, SegmentationData]) -> None:
        for guid, new_entry in data.items():
            if not self.image_exists(new_entry.file_path):
                self.project.data[new_entry.guid] = new_entry

    def add(self, data: Dict[UUID, SegmentationData]) -> None:
        for guid, new_entry in data.items():
            if not self.image_exists(new_entry.file_path):
                self.project.data[new_entry.guid] = new_entry


    def set_classes(self, classes: List[str]):
        self.project.classes = classes

    def get_data_by_guid(self, guid: UUID) -> SegmentationData | None:
        for _guid, _data in self.project.data.items():
            if guid == _guid:
                return _data

        return None

    def add_mask_data(self, image_guid: UUID, mask: Image.Image):
        _mask = Mask(
            guid=generate_uuid(),
            x=self.project.data[image_guid].x,
            y=self.project.data[image_guid].y,
            image=mask)

        # zero-ing out the main image as well since an automatically resized bbox can cause offsets when trying to move it back to the original position
        self.project.data[image_guid].x = 0
        self.project.data[image_guid].y = 0
        self.project.data[image_guid].mask.image = mask

    def get_mask_data(self, image_guid: UUID) -> Mask | None:
        for guid, entry in self.project.data.items():
            if image_guid == guid:
                return entry.mask
        return None

    def add_anchor(self, image_guid: UUID, anchor: Anchor):
        for guid, entry in self.project.data.items():
            if image_guid == guid:
                entry.anchors.append(anchor)

    def remove_anchor(self, image_guid: UUID, anchor: Anchor):
        for guid, entry in self.project.data.items():
            if image_guid == guid:
                if anchor in entry.anchors:
                    entry.anchors.remove(anchor)
                else:
                    print(f"WARNING: Tried to remove a non-existing anchor")

    def add_bbox(self, image_guid: UUID, bbox: BBox):
        for guid, entry in self.project.data.items():
            if image_guid == guid:
                entry.bboxes.append(bbox)

    def remove_bbox(self, image_guid: UUID, bbox: BBox):
        for guid, entry in self.project.data.items():
            if image_guid == guid:
                if bbox in entry.bboxes:
                    entry.bboxes.remove(bbox)
                else:
                    print(f"WARNING: Tried to remove a non-existing BBox")

    def update_bbox_state(self, image_guid: UUID, state: BBoxState):
        for _bbox in self.project.data[image_guid].bboxes:
            if _bbox.guid == state.guid:
                _bbox.active = state.active

    def update_bbox_label(self, image_guid: UUID, bbox_guid: UUID, label: str):
        for _bbox in self.project.data[image_guid].bboxes:
            if _bbox.guid == bbox_guid:
                _bbox.name = label
                if not label in self.project.classes:
                    self.project.classes.append(label)
                    self.cleanup_classes()
                return

    def cleanup_classes(self):
        """
        A simple workaround to clean-up the class index to make sure no unsused bbox labels are in the project's class list
        """
        _classes = []

        for _, entry in self.project.data.items():
            for bbox in entry.bboxes:
                if bbox.name not in _classes:
                    _classes.append(bbox.name)

        self.project.classes = _classes

    def update_image_position(self, image_position: ImagePosition):
        if self.project.data is None or len(self.project.data) == 0:
            return

        for _guid, _data in self.project.data.items():
            if _guid == image_position.guid:
                _data.x = image_position.x
                _data.y = image_position.y


    def update_mask_position(self, mask_position: MaskPosition):
        for _guid, _data in self.project.data.items():
            if _data.mask.guid == mask_position.guid:
                _data.mask.x = mask_position.x
                _data.mask.y = mask_position.y


    def update_bbox_position(self, image_guid: UUID, bbox_position: BBoxPosition):
        if self.project.data is None or len(self.project.data) == 0:
            return

        for _bbox in self.project.data[image_guid].bboxes:
            if _bbox.guid == bbox_position.guid:
                _bbox.x = bbox_position.x
                _bbox.y = bbox_position.y
                _bbox.w = bbox_position.w
                _bbox.h = bbox_position.h

    def update_anchor_position(self, image_guid: UUID, anchor_position: AnchorPosition):
        if self.project.data is None or len(self.project.data) == 0:
            return

        for _anchor in self.project.data[image_guid].anchors:
            if _anchor.guid == anchor_position.guid:
                _anchor.x = anchor_position.x
                _anchor.y = anchor_position.y

    def update_sam_result(self, result: SamResult):
        for _guid, _data in self.project.data.items():
            if result.image_guid == _guid:
                if result.bbox is not None:
                    for _bbox in _data.bboxes:
                        if result.bbox.guid == _bbox.guid:
                            _bbox.x = result.bbox.x
                            _bbox.y = result.bbox.y
                            _bbox.w = result.bbox.w
                            _bbox.h = result.bbox.h

                if result.anchors is not None:
                    for _project_anchor in _data.anchors:
                        for _result_anchor in result.anchors:
                            if _result_anchor.guid == _project_anchor.guid:
                                _project_anchor.x = _result_anchor.x
                                _project_anchor.y = _result_anchor.y

                _data.mask.x = 0
                _data.mask.y = 0
                _data.mask.image = result.mask

                # zero-ing out the original image and mask to avoid offsets, maybe change that later
                _data.x = 0
                _data.y = 0

    def update_sam_batch_result(self, result: BatchSamResult):
        for _guid, _data in self.project.data.items():
            if result.image_guid == _guid:
                for _bbox in _data.bboxes:
                    for _result_bbox in result.bboxes:
                        if _result_bbox.guid == _bbox.guid:
                            _bbox.x = _result_bbox.x
                            _bbox.y = _result_bbox.y
                            _bbox.w = _result_bbox.w
                            _bbox.h = _result_bbox.h

                # zero-ing out the original image and mask to avoid offsets, maybe change that later
                _data.mask.x = 0
                _data.mask.y = 0
                _data.mask.image = result.mask

                _data.x = 0
                _data.y = 0

    def update_zoom_level(self, zoom_level: ZoomLevel):
        print(f"Updating ZoomLevel: {zoom_level.image_guid}, zoom level: {zoom_level.factor}")
        for _guid, _data in self.project.data.items():
            if _guid == zoom_level.image_guid:
                _data.zoom = zoom_level.factor

    def delete_item(self, guid: UUID):
        for _guid, _data in self.project.data.items():
            if _guid == guid:
                self.project.data.pop(_guid)
                return

            for _anchor in _data.anchors:
                if _anchor.guid == guid:
                    _data.anchors.remove(_anchor)
                    return

            for _bbox in _data.bboxes:
                if _bbox.guid == guid:
                    _data.bboxes.remove(_bbox)
                    return

    def delete_annotations(self, image_guid: UUID):
        keys = list(self.project.data.keys())

        if image_guid in keys:
            self.project.data[image_guid].bboxes = []
            self.project.data[image_guid].anchors = []

        else:
            print(f"WARNING: Tried to delete annotations for non-existing image guid: {image_guid}")

    def delete_all_images(self):
        self.project.data = {}