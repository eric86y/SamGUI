from PIL import Image
from enum import Enum
from uuid import UUID
from typing import Dict, List
from dataclasses import dataclass


class AddOP(Enum):
    SUCCESS = 0
    FAILED = 1
    EXIST = 2


class Tool(Enum):
    Selection = 0
    Anchor = 1
    BBOX = 2

class SAMMode(Enum):
    anchors = 0
    bbox = 1

class Edge(Enum):
    Left = 0
    Right = 1
    Top = 2
    Bottom = 3


@dataclass
class ScreenData:
    max_width: int
    max_height: int
    start_width: int
    start_height: int
    start_x: int
    start_y: int

@dataclass
class Label:
    background = 0
    foreground = 1

@dataclass
class ImagePosition:
    guid: UUID
    x: int
    y: int

@dataclass
class MaskPosition:
    guid: UUID
    x: int
    y: int

@dataclass
class Anchor:
    guid: UUID
    class_id: Label
    active: bool
    x: int
    y: int

@dataclass
class AnchorState:
    guid: UUID
    active: bool

@dataclass
class BBoxState:
    guid: UUID
    active: bool


@dataclass
class AnchorPosition:
    guid: UUID
    x: int
    y: int

@dataclass
class CroppedExportData:
    file_name: str
    images: List
    masks: List

@dataclass
class MaskExportData:
    file_name: str
    masks: List

@dataclass
class BBox:
    guid: UUID
    name: str
    active: bool
    x: float
    y: float
    w: float
    h: float

@dataclass
class BBoxPosition:
    guid: UUID
    x: float
    y: float
    w: float
    h: float

@dataclass
class BBoxLabel:
    guid: UUID
    label: str

@dataclass
class Mask:
    guid: UUID
    x: int
    y: int
    image: Image.Image | None


@dataclass
class SegmentationData:
    guid: UUID
    file_path: str
    file_name: str
    x: int
    y: int
    anchors: List[Anchor]
    bboxes: List[BBox]
    mask: Mask | None
    zoom: float


@dataclass
class ProjectData:
    guid: UUID
    name: str
    classes: List[str]
    data: Dict[UUID, SegmentationData]


@dataclass
class YoloAnnotation:
    class_id: int
    center_x: float
    center_y: float
    width: float
    height: float


@dataclass
class YoloAnnotations:
    file_name: str
    classes: List[str]
    annotations: List[YoloAnnotation]


@dataclass
class SamResult:
    image_guid: UUID
    mask: Image.Image
    bbox: BBox | None
    anchors: List[Anchor] | None


@dataclass
class BatchSamResult:
    image_guid: UUID
    mask: Image.Image
    bboxes: List[BBox]

@dataclass
class ZoomLevel:
    image_guid: UUID
    factor: float

@dataclass
class ErrorMessage:
    type: str
    message: str
