"""图片编辑功能：缩放与裁剪。

每个函数只做一件事：接收 ndarray、校验参数、返回新的 ndarray；
参数不合法时抛 ImageToolError，由 CLI 统一打印提示。
"""
from __future__ import annotations

import cv2
import numpy as np

from .utils import ImageToolError


def parse_box(text: str) -> tuple[int, int, int, int]:
    """解析「左,上,右,下」四个整数坐标。"""
    parts = text.split(",")
    if len(parts) != 4:
        raise ImageToolError(f"裁剪区域需要 4 个整数（左,上,右,下），收到：{text!r}")
    try:
        left, top, right, bottom = (int(part.strip()) for part in parts)
    except ValueError as exc:
        raise ImageToolError(f"裁剪坐标必须是整数：{text!r}") from exc
    return left, top, right, bottom


def resize_image(image: np.ndarray, width: int | None,
                 height: int | None) -> np.ndarray:
    """指定宽高缩放；只给宽或只给高时，另一边按原图比例自动计算。"""
    if width is None and height is None:
        raise ImageToolError("缩放至少需要指定 --width 或 --height 中的一个")
    if width is not None and width <= 0:
        raise ImageToolError(f"宽度必须是大于 0 的整数，收到：{width}")
    if height is not None and height <= 0:
        raise ImageToolError(f"高度必须是大于 0 的整数，收到：{height}")

    src_h, src_w = image.shape[:2]
    if width is None:
        width = max(1, round(src_w * height / src_h))
    elif height is None:
        height = max(1, round(src_h * width / src_w))
    # 缩小用 INTER_AREA 更平滑，放大用 INTER_LINEAR
    interpolation = cv2.INTER_AREA if (width < src_w or height < src_h) else cv2.INTER_LINEAR
    result = cv2.resize(image, (width, height), interpolation=interpolation)
    print(f"缩放完成：{src_w} x {src_h} → {width} x {height} 像素")
    return result


def crop_image(image: np.ndarray, left: int, top: int,
               right: int, bottom: int) -> np.ndarray:
    """按「左,上,右,下」裁剪；区域越界时给出带实际尺寸的明确提示。"""
    src_h, src_w = image.shape[:2]
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise ImageToolError(
            f"裁剪区域不合法：({left}, {top}, {right}, {bottom})；"
            "需满足 0 <= 左 < 右、0 <= 上 < 下"
        )
    if right > src_w or bottom > src_h:
        raise ImageToolError(
            f"裁剪区域越界：图片尺寸为 {src_w} x {src_h} 像素，"
            f"但区域右下角是 ({right}, {bottom})"
        )
    result = image[top:bottom, left:right].copy()
    print(f"裁剪完成：区域 ({left}, {top}, {right}, {bottom})，"
          f"结果 {result.shape[1]} x {result.shape[0]} 像素")
    return result


ROTATION_ANGLES = (90, 180, 270)
FLIP_DIRECTIONS = ("horizontal", "vertical", "both")
TARGET_FORMATS = {
    "png": ".png",
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "bmp": ".bmp",
    "webp": ".webp",
}


def rotate_image(image: np.ndarray, angle: int) -> np.ndarray:
    """旋转图片，至少支持 90 / 180 / 270 度（90 与 270 会交换宽高）。"""
    if angle not in ROTATION_ANGLES:
        raise ImageToolError(f"暂不支持 {angle} 度旋转；仅支持 90、180、270 度")
    codes = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }
    result = cv2.rotate(image, codes[angle])
    print(f"旋转完成：{angle} 度，结果 {result.shape[1]} x {result.shape[0]} 像素")
    return result


def flip_image(image: np.ndarray, direction: str) -> np.ndarray:
    """水平翻转 / 垂直翻转 / 两者同时。"""
    codes = {"horizontal": 1, "vertical": 0, "both": -1}
    if direction not in codes:
        raise ImageToolError(f"不支持的翻转方向：{direction}（可用 {', '.join(FLIP_DIRECTIONS)}）")
    result = cv2.flip(image, codes[direction])
    print(f"翻转完成：{direction}")
    return result


def grayscale_image(image: np.ndarray) -> np.ndarray:
    """彩色图转灰度图；已经是灰度图时原样输出并给出提示。"""
    if image.ndim == 2:
        print("该图片本身已是灰度图，直接输出结果")
        return image.copy()
    channels = image.shape[2]
    if channels == 3:
        result = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif channels == 4:
        result = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    elif channels == 2:  # 灰度 + Alpha：丢弃透明通道，保留灰度
        result = cv2.split(image)[0].copy()
    else:
        raise ImageToolError(f"无法把 {channels} 通道图像转换成灰度图")
    print(f"灰度化完成：结果 {result.shape[1]} x {result.shape[0]} 像素（单通道）")
    return result


def target_extension(target: str) -> str:
    """把目标格式名映射成文件扩展名。"""
    key = target.lower().lstrip(".")
    if key not in TARGET_FORMATS:
        raise ImageToolError(
            f"不支持的目标格式：{target}（可用 {', '.join(sorted(TARGET_FORMATS))}）"
        )
    return TARGET_FORMATS[key]
