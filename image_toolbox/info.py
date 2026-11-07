"""读取图片基础信息：文件名、格式、宽高、颜色模式、文件大小。"""
from __future__ import annotations

from pathlib import Path

from .utils import ImageToolError, color_mode, load_image

# 常见图片格式的文件头魔数，比只看扩展名更可靠
_MAGIC: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"\xff\xd8\xff", "JPEG"),
    (b"BM", "BMP"),
    (b"GIF87a", "GIF"),
    (b"GIF89a", "GIF"),
    (b"II*\x00", "TIFF"),
    (b"MM\x00*", "TIFF"),
    (b"RIFF", "WEBP"),  # RIFF....WEBP 时进一步确认
]


def detect_format(path: Path) -> str:
    """优先按文件头判断格式，判断不出来时退回扩展名。"""
    try:
        head = path.read_bytes()[:16]
    except OSError as exc:
        raise ImageToolError(f"无法读取文件内容：{path}（{exc}）") from exc
    for magic, name in _MAGIC:
        if head.startswith(magic):
            if name == "WEBP" and b"WEBP" not in head:
                continue
            return name
    suffix = path.suffix.lstrip(".").upper()
    return suffix if suffix else "未知"


def human_size(path: Path) -> str:
    """文件大小：不足 1 MB 用 KB，否则用 MB，均保留 2 位小数。"""
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    return f"{size / 1024:.2f} KB"


def collect_info(path_str: str) -> dict[str, str]:
    """汇总成字典，便于复用与测试。"""
    image, path = load_image(path_str)
    height, width = image.shape[:2]
    return {
        "文件名": path.name,
        "图片格式": detect_format(path),
        "宽度和高度": f"{width} x {height} 像素",
        "颜色模式": color_mode(image),
        "文件大小": human_size(path),
    }


def show_info(path_str: str) -> None:
    """把图片信息以对齐的表格打印到终端。"""
    info = collect_info(path_str)
    print("图片基础信息")
    print("-" * 42)
    width = max(len(key) for key in info)
    for key, value in info.items():
        print(f"{key:<{width}}  {value}")
