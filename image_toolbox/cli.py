"""命令行参数解析与分发。

所有可预期的错误统一收敛为 ImageToolError / OSError，
打印友好提示并返回退出码 1，不把 Python 堆栈暴露给使用者。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from .edits import (
    FLIP_DIRECTIONS,
    TARGET_FORMATS,
    crop_image,
    flip_image,
    grayscale_image,
    parse_box,
    resize_image,
    rotate_image,
    target_extension,
)
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

    p_rotate = sub.add_parser("rotate", help="旋转图片（90 / 180 / 270 度）")
    p_rotate.add_argument("image", help="图片文件路径")
    p_rotate.add_argument("-a", "--angle", type=int, required=True,
                          help="旋转角度：90 / 180 / 270")
    _add_output(p_rotate)

    p_flip = sub.add_parser("flip", help="水平或垂直翻转图片")
    p_flip.add_argument("image", help="图片文件路径")
    p_flip.add_argument("-d", "--direction", choices=list(FLIP_DIRECTIONS),
                        default="horizontal", help="翻转方向，默认 horizontal")
    _add_output(p_flip)

    p_gray = sub.add_parser("grayscale", help="彩色图转灰度图")
    p_gray.add_argument("image", help="图片文件路径")
    _add_output(p_gray)

    p_convert = sub.add_parser("convert", help="格式转换，例如 PNG 与 JPG 互转")
    p_convert.add_argument("image", help="图片文件路径")
    p_convert.add_argument("-t", "--to", choices=sorted(TARGET_FORMATS), required=True,
                           help="目标格式：png / jpg / jpeg / bmp / webp")
    _add_output(p_convert)

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
        elif args.command == "rotate":
            result = rotate_image(image, args.angle)
            _save_result(result, source, args, f"rotated{args.angle}")
        elif args.command == "flip":
            result = flip_image(image, args.direction)
            _save_result(result, source, args, f"flipped_{args.direction}")
        elif args.command == "grayscale":
            result = grayscale_image(image)
            _save_result(result, source, args, "grayscale")
        elif args.command == "convert":
            ext = target_extension(args.to)
            _save_result(image, source, args, "converted", ext)
    except (ImageToolError, OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # 兜底：任何未预期异常也不让程序直接崩溃
        print(f"[错误] 发生未预期的错误：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
