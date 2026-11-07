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


OUTPUT_DIR_NAME = "output"
WRITABLE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}


def resolve_output(source: Path, requested: str | None, suffix: str,
                   ext: str | None = None) -> Path:
    """决定输出路径：默认保存到源文件同级 output/ 目录，绝不覆盖原图。"""
    if requested:
        out = Path(requested).expanduser()
        if not out.suffix:
            raise ImageToolError(f"输出路径缺少扩展名：{out}")
    else:
        out = source.parent / OUTPUT_DIR_NAME / f"{source.stem}_{suffix}{ext or source.suffix}"
    # 硬约束：编辑结果只能另存为新文件，不能覆盖原图
    try:
        if out.resolve() == source.resolve():
            raise ImageToolError("输出路径与原图相同，已拒绝；本程序不会覆盖原图")
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ImageToolError(f"无法创建或解析输出路径：{out}（{exc}）") from exc
    return out


def to_bgr_for_jpeg(image: np.ndarray) -> np.ndarray:
    """带透明通道的 PNG 存成 JPG 前，先以白底合成再转成 3 通道 RGB(BGR)。"""
    if image.ndim == 2:  # 灰度
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    channels = image.shape[2]
    if channels == 3:
        return image
    if channels == 4:  # BGRA
        b, g, r, a = cv2.split(image)
        alpha = (a.astype(np.float32) / 255.0)[:, :, None]
        color = np.stack([b, g, r], axis=2).astype(np.float32)
        merged = color * alpha + 255.0 * (1.0 - alpha)
        return np.clip(merged, 0, 255).astype(np.uint8)
    if channels == 2:  # 灰度 + Alpha
        gray, a = cv2.split(image)
        alpha = a.astype(np.float32) / 255.0
        merged = gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)
        return cv2.cvtColor(np.clip(merged, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    raise ImageToolError(f"无法把 {channels} 通道图像转换成 JPG 所需的 RGB 图像")


def save_image(image: np.ndarray, out: Path) -> None:
    """把编辑结果写入新文件；失败时给出明确提示而不是崩溃。"""
    ext = out.suffix.lower()
    if ext not in WRITABLE_SUFFIXES:
        raise ImageToolError(f"不支持的输出格式：{ext}（可用 png/jpg/bmp/webp/tif）")
    try:
        params = []
        if ext in (".jpg", ".jpeg"):
            image = to_bgr_for_jpeg(image)  # JPG 无透明通道，必须先转 RGB
            params = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        ok = cv2.imwrite(str(out), image, params)
    except cv2.error as exc:
        raise ImageToolError(f"保存图片失败：{out}（{exc}）") from exc
    if not ok:
        raise ImageToolError(f"保存图片失败：{out}（编码器不支持该图像或路径不可写）")
    print(f"已保存：{out.resolve()}")
