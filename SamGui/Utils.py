import os
import cv2
import uuid
import logging
import numpy as np
import numpy.typing as npt
from PySide6.QtWidgets import QApplication

from SamGui.Data import BBox, ScreenData
from datetime import datetime
from PIL import Image, ImageOps
from typing import List


def has_data(a: dict | list) -> bool:
    if a is not None and len(a) > 0:
        return True
    else:
        return False

def get_screen_center(app: QApplication, start_size_ratio: float = 0.8) -> ScreenData:
    screen = app.primaryScreen()
    rect = screen.availableGeometry()
    max_width = rect.width()
    max_height = rect.height()

    start_width = int(rect.width() * start_size_ratio)
    start_height = int(rect.height() * start_size_ratio)

    start_pos_x = (max_width - start_width) // 2
    start_pos_y = (max_height - start_height) // 2

    screen_data = ScreenData(
        max_width=max_width,
        max_height=max_height,
        start_width=start_width,
        start_height=start_height,
        start_x=start_pos_x,
        start_y=start_pos_y,
    )

    return screen_data

def get_filename(file_path: str) -> str:
    name_segments = os.path.basename(file_path).split(".")[:-1]
    name = "".join(f"{x}." for x in name_segments)
    return name.rstrip(".")

def get_file_extension(file_path: str) -> str:
    extension = os.path.basename(file_path).split(".")[-1]
    extension = extension.strip()
    return extension

def get_timestamp() -> str:
    time = datetime.now()
    stamp = f"{time.year}_{time.month}_{time.day}_{time.hour}_{time.minute}"
    return stamp

def create_dir(dir_path: str) -> None:
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created output directory: {dir_path}")
    except BaseException as e:
        logging.error(f"Failed to create directory: {e}")


def generate_uuid() -> uuid.UUID:
    return uuid.uuid1()

def convert_transparent_mask_to_binary(
    mask: Image.Image, threshold: int = 80
) -> Image.Image:
    mask = mask.point(lambda x: 255 if x > threshold else 0)
    mask = mask.convert("1")
    return mask


def convert_png2jpeg(image: Image.Image) -> Image.Image:
    jpg_image = Image.new("RGB", image.size, (255, 255, 255))
    jpg_image.paste(image, mask=image.split()[3])

    return jpg_image


def mask_region(image: Image.Image) -> Image.Image:
    """
    Meant to roughly isolate the returned mask to generate a reasonable Thumbnail
    """
    np_image = np.array(image)
    np_image = cv2.bitwise_not(np_image)
    np_image = np.delete(np_image, np.where(~np_image.any(axis=1))[0], axis=0)
    np_image = np.delete(np_image, np.where(~np_image.any(axis=0))[0], axis=1)
    np_image = cv2.bitwise_not(np_image)

    pil_image = Image.fromarray(np_image)
    return pil_image


def convert_sam_to_mask(sam_mask: Image.Image, area_threshold: int = 4) -> npt.NDArray:
    mask = np.array(sam_mask)
    mask = np.where(mask == 0, 1.0, 0.0)
    mask *= 255
    mask = mask.astype(np.uint8)
    mask_contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours = [
        contour for contour in mask_contours if cv2.contourArea(contour) > area_threshold
    ]
    mask_img = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    cv2.drawContours(mask_img, filtered_contours, -1, (255, 255, 255), -1)

    return mask_img


def generate_alpha_mask(input_mask: Image.Image) -> Image.Image:

    grayscale_mask = input_mask.convert("L")
    alpha_mask = ImageOps.colorize(grayscale_mask, black="black", white="red")
    alpha_mask = alpha_mask.convert("RGBA")

    array = np.array(alpha_mask, dtype=np.uint8)
    is_black = (array[:, :, :3] == (0, 0, 0)).all(axis=2)
    alpha = np.where(is_black, 0, 255)
    array[:, :, -1] = alpha

    alpha_mask = Image.fromarray(array, "RGBA")
    alpha_mask.putalpha(128)

    return alpha_mask

def create_crop_image(image: Image.Image, bbox: BBox, x_pos: int, y_pos: int):
    x_delta = bbox.x + (x_pos * -1)
    y_delta = bbox.y + (y_pos * -1)

    crop_img = image.crop((x_delta, y_delta, x_delta + bbox.w, y_delta + bbox.h))
    return crop_img


def read_class_file(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        classes = f.readlines()
        classes = [x.replace("\n", "") for x in classes]

        return classes