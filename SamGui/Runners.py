import os
import cv2
import sys
import traceback
import numpy as np

import onnxruntime as ort
import numpy.typing as npt

from PIL import Image
from copy import deepcopy
from typing import List
from PySide6.QtCore import QRunnable
from SamGui.Controller import WorkerSignals
from SamGui.Data import SegmentationData, SAMMode, Anchor, Label, SamResult, BBox, BatchSamResult, ErrorMessage


class SAMRunner(QRunnable):
    def __init__(self, data: SegmentationData, mode: SAMMode, adjust_bbox: bool, encoder_path: str, decoder_path: str):
        super(SAMRunner, self).__init__()
        self.data = data
        self.mode = mode
        self.adjust_bbox = adjust_bbox
        self.signals = WorkerSignals()

        self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.encoder_path = encoder_path
        self.decoder_path = decoder_path

        self.encoder = ort.InferenceSession(self.encoder_path)
        self.decoder = ort.InferenceSession(self.decoder_path)

        

    def process_anchors(self,
                        embeddings: npt.NDArray,
                        input_pts: List[List[int]],
                        input_labels: List[Label],
                        resized_width: int,
                        resized_height: int,
                        orig_width: int,
                        orig_height: int) -> Image.Image:

        input_point = np.array(input_pts)
        input_label = np.array(input_labels)

        onnx_coord = np.concatenate([input_point, np.array([[0.0, 0.0]])], axis=0)[
                     None, :, :
                     ]
        onnx_label = np.concatenate([input_label, np.array([-1])])[None, :].astype(
            np.float32
        )

        coords = deepcopy(onnx_coord).astype(float)
        coords[..., 0] = coords[..., 0] * (resized_width / orig_width)
        coords[..., 1] = coords[..., 1] * (resized_height / orig_height)

        onnx_coord = coords.astype("float32")
        onnx_mask_input = np.zeros((1, 1, 256, 256), dtype=np.float32)
        onnx_has_mask_input = np.zeros(1, dtype=np.float32)

        outputs = self.decoder.run(
            None,
            {
                "image_embeddings": embeddings,
                "point_coords": onnx_coord,
                "point_labels": onnx_label,
                "mask_input": onnx_mask_input,
                "has_mask_input": onnx_has_mask_input,
                "orig_im_size": np.array(
                    [orig_height, orig_width], dtype=np.float32
                )
            },
        )
        masks = outputs[0]

        mask = masks[0][0]
        mask = (mask > 0).astype("uint8") * 255
        mask = Image.fromarray(mask)

        return mask

    def process_bbox(self,
                     embeddings: npt.NDArray,
                     bbox: BBox,
                     resized_width: int,
                     resized_height: int,
                     orig_width: int,
                     orig_height: int):
        coords = [bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h]
        input_box = np.array(coords).reshape(2, 2)
        box_labels = np.array([2, 3])

        onnx_coord = np.array([input_box], dtype=np.float32)
        onnx_label = box_labels[None, :].astype(np.float32)

        assert orig_width != 0 and orig_height != 0

        coords = deepcopy(onnx_coord).astype(float)
        coords[..., 0] *= resized_width / orig_width
        coords[..., 1] *= resized_height / orig_height
        onnx_coord = np.array(coords, dtype=np.float32)

        onnx_mask_input = np.zeros((1, 1, 256, 256), dtype=np.float32)
        onnx_has_mask_input = np.zeros(1, dtype=np.float32)

        outputs = self.decoder.run(None, {
            "image_embeddings": embeddings,
            "point_coords": onnx_coord,
            "point_labels": onnx_label,
            "mask_input": onnx_mask_input,
            "has_mask_input": onnx_has_mask_input,
            "orig_im_size": np.array([orig_height, orig_width], dtype=np.float32),
        })

        masks = outputs[0]
        mask = masks[0][0]
        mask = (mask > 0).astype('uint8') * 255

        return mask

    @staticmethod
    def correct_bbox(mask: npt.NDArray):
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        area_sizes = [cv2.contourArea(x) for x in contours]
        biggest_contour = contours[area_sizes.index(max(area_sizes))]
        x, y, w, h = cv2.boundingRect(biggest_contour)

        return x, y, w, h


    def run(self):
        assert os.path.isfile(self.data.file_path)

        try:
            img = Image.open(self.data.file_path).convert("RGB")
            orig_width, orig_height = img.size

            if orig_width > orig_height:
                resized_width = 1024
                resized_height = int(1024 / orig_width * orig_height)
            else:
                resized_height = 1024
                resized_width = int(1024 / orig_height * orig_width)

            img = img.resize((resized_width, resized_height), Image.Resampling.BILINEAR)

            input_tensor = np.array(img)
            mean = np.array([123.675, 116.28, 103.53])
            std = np.array([[58.395, 57.12, 57.375]])
            input_tensor = (input_tensor - mean) / std

            # Transpose input tensor to shape BxCxHxW
            input_tensor = input_tensor.transpose(2, 0, 1)[None, :, :, :].astype(
                np.float32
            )

            if resized_height < resized_width:
                input_tensor = np.pad(
                    input_tensor, ((0, 0), (0, 0), (0, 1024 - resized_height), (0, 0))
                )
            else:
                input_tensor = np.pad(
                    input_tensor, ((0, 0), (0, 0), (0, 0), (0, 1024 - resized_width))
                )

            outputs = self.encoder.run(None, {"images": input_tensor})
            embeddings = outputs[0]

            x_delta = self.data.x * -1
            y_delta = self.data.y * -1

            _input_pts = []
            _input_lbls = []

            _norm_bboxes = []
            _norm_anchors = []

            for _anchor in self.data.anchors:
                _x = _anchor.x + x_delta
                _y = _anchor.y + y_delta

                _n_anchor = Anchor(
                    guid=_anchor.guid,
                    class_id=_anchor.class_id,
                    active=_anchor.active,
                    x=_x,
                    y=_y
                )

                _input_pts.append([_x, _y])
                _input_lbls.append(_anchor.class_id)
                _norm_anchors.append(_n_anchor)

            for _bbox in self.data.bboxes:
                if _bbox.active:
                    _x = _bbox.x + x_delta
                    _y = _bbox.y + y_delta

                    _n_box = [_x, _y, _x + _bbox.w, _y + _bbox.h]
                    _norm_bboxes.append(_n_box)

            if self.mode == SAMMode.anchors:
                mask = self.process_anchors(
                    embeddings,
                    _input_pts,
                    _input_lbls,
                    resized_width,
                    resized_height,
                    orig_width,
                    orig_height
                )

                sam_result = SamResult(
                    image_guid=self.data.guid,
                    mask=mask,
                    bbox=None,
                    anchors=_norm_anchors
                )

                self.signals.s_sam_result.emit(sam_result)


            elif self.mode == SAMMode.bbox:
                if len(self.data.bboxes) == 1:
                    _bbox = self.data.bboxes[0]

                    _x = _bbox.x + x_delta
                    _y = _bbox.y + y_delta
                    norm_bbox = BBox(_bbox.guid, _bbox.name, _bbox.active, _x, _y, _bbox.w, _bbox.h)
                    mask = self.process_bbox(embeddings, norm_bbox, resized_width, resized_height, orig_width, orig_height)

                    if self.adjust_bbox:
                        x, y, w, h = self.correct_bbox(mask)

                        bbox = BBox(
                            guid=_bbox.guid,
                            active=True,
                            name=_bbox.name,
                            x=x,
                            y=y,
                            w=w,
                            h=h
                        )
                        mask = Image.fromarray(mask)
                        sam_result = SamResult(
                            image_guid=self.data.guid,
                            mask=mask,
                            bbox=bbox,
                            anchors=_norm_anchors
                        )

                        self.signals.s_sam_result.emit(sam_result)
                    else:
                        mask = Image.fromarray(mask)
                        sam_result = SamResult(
                            image_guid=self.data.guid,
                            mask=mask,
                            bbox=_bbox,
                            anchors=_norm_anchors
                        )
                        self.signals.s_sam_result.emit(sam_result) # returns everything with (0,0) origin

                if len(self.data.bboxes) > 1:
                    results = []

                    for _bbox in self.data.bboxes:
                        _x = _bbox.x + x_delta
                        _y = _bbox.y + y_delta
                        norm_bbox = BBox(_bbox.guid, _bbox.name, _bbox.active, _x, _y, _bbox.w, _bbox.h)

                        mask = self.process_bbox(
                            embeddings,
                            norm_bbox,
                            resized_width,
                            resized_height,
                            orig_width,
                            orig_height
                        )

                        if self.adjust_bbox:
                            x, y, w, h = self.correct_bbox(mask)
                            mask = Image.fromarray(mask)

                            bbox = BBox(
                                guid=_bbox.guid,
                                active=True,
                                name=_bbox.name,
                                x=x,
                                y=y,
                                w=w,
                                h=h
                            )

                            sam_result = SamResult(
                                image_guid=self.data.guid,
                                mask=mask,
                                bbox=bbox,
                                anchors=_norm_anchors
                            )

                            results.append(sam_result)
                        else:
                            sam_result = SamResult(
                                image_guid=self.data.guid,
                                mask=Image.fromarray(mask),
                                bbox=norm_bbox,
                                anchors=_norm_anchors
                            )

                            results.append(sam_result) # returns everything with (0,0) origin

                    all_masks = [x.mask for x in results]
                    all_masks = [np.array(x) for x in all_masks]
                    stack = np.dstack(all_masks)
                    concat_mask = np.sum(stack, axis=-1)
                    all_boxes = [x.bbox for x in results]

                    concat_mask = (concat_mask > 0).astype('uint8') * 255
                    concat_mask = Image.fromarray(concat_mask, "L")

                    batch_result = BatchSamResult(
                        image_guid=self.data.guid,
                        mask=concat_mask,
                        bboxes=all_boxes
                    )
                    self.signals.s_sam_batch_result.emit(batch_result) # returns everything with (0,0) origin

        except BaseException as e:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]

            error_msg = ErrorMessage(
                type=exctype,
                message=value
            )
            self.signals.s_error.emit(error_msg)

        else:
            pass
        finally:
            self.signals.s_finished.emit()