"""命令行参数解析与分发。

所有命令的错误统一收敛为 ImageToolError，打印友好提示并返回退出码 1。
"""
from __future__ import annotations

import argparse
import sys

from .info import show_info
from .utils import ImageToolError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_tool.py",
        description="读取图片基础信息并完成简单图片编辑（基于 OpenCV）",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="命令")

    p_info = sub.add_parser("info", help="读取并显示图片基础信息")
    p_info.add_argument("image", help="图片文件路径")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            show_info(args.image)
    except ImageToolError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
