"""通用工具：可预期的业务异常与图片读取。

所有面向使用者的错误都抛 ImageToolError，由 CLI 统一打印提示，
避免把 Python 堆栈直接暴露给使用者。
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class ImageToolError(Exception):
    """面向使用者的错误：打印友好提示，不打印堆栈。"""


def load_image(path_str: str) -> tuple[np.ndarray, Path]:
    """读取图片；保留透明通道（IMREAD_UNCHANGED），失败时给出明确提示。"""
    path = Path(path_str).expanduser()
    if not path.exists():
        raise ImageToolError(f"文件不存在：{path}")
    if not path.is_file():
        raise ImageToolError(f"路径不是一个文件：{path}")
    try:
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    except cv2.error as exc:  # OpenCV 解码异常也收敛成友好提示
        raise ImageToolError(f"读取图片失败：{path}（{exc}）") from exc
    if image is None or image.size == 0:
        raise ImageToolError(f"文件不是有效图片或该格式不受支持：{path}")
    return image, path


def color_mode(image: np.ndarray) -> str:
    """按通道数给出人能看懂的颜色模式名称。"""
    if image.ndim == 2:
        return "灰度 GRAY（1 通道）"
    channels = image.shape[2]
    return {
        2: "灰度 + Alpha LA（2 通道）",
        3: "RGB（3 通道）",
        4: "RGBA（4 通道，含透明通道）",
    }.get(channels, f"{channels} 通道")
