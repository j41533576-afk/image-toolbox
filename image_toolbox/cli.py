"""命令行参数解析与分发。

所有命令的错误统一收敛为 ImageToolError，打印友好提示并返回退出码 1。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from .edits import crop_image, parse_box, resize_image
from .info import show_info
from .utils import ImageToolError, load_image, resolve_output, save_image


def _add_output(parser: argparse.ArgumentParser) -> None:
    """给编辑命令统一添加 -o/--output 参数。"""
    parser.add_argument("-o", "--output", help="结果文件路径；不填则自动保存到 output/ 目录")


def _save_result(image: np.ndarray, source: Path, args: argparse.Namespace,
                 suffix: str, ext: str | None = None) -> None:
    """把编辑结果另存为新文件，并打印保存位置。"""
    out = resolve_output(source, args.output, suffix, ext)
    save_image(image, out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_tool.py",
        description="读取图片基础信息并完成简单图片编辑（基于 OpenCV）",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="命令")

    p_info = sub.add_parser("info", help="读取并显示图片基础信息")
    p_info.add_argument("image", help="图片文件路径")

    p_resize = sub.add_parser("resize", help="缩放图片，只给宽或高时按比例缩放")
    p_resize.add_argument("image", help="图片文件路径")
    p_resize.add_argument("-W", "--width", type=int, help="目标宽度（像素）")
    p_resize.add_argument("-H", "--height", type=int, help="目标高度（像素）")
    _add_output(p_resize)

    p_crop = sub.add_parser("crop", help="裁剪图片，区域为 左,上,右,下")
    p_crop.add_argument("image", help="图片文件路径")
    p_crop.add_argument("-b", "--box", required=True, help="裁剪区域，例如 10,20,300,240")
    _add_output(p_crop)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            show_info(args.image)
            return 0

        image, source = load_image(args.image)
        if args.command == "resize":
            result = resize_image(image, args.width, args.height)
            _save_result(result, source, args, "resized")
        elif args.command == "crop":
            left, top, right, bottom = parse_box(args.box)
            result = crop_image(image, left, top, right, bottom)
            _save_result(result, source, args, "cropped")
    except ImageToolError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
