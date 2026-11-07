"""冒烟测试：自动生成临时图片，逐条验证所有命令与错误提示。

运行方式（在仓库根目录）：
    uv run python tests/smoke_test.py

测试图片在临时目录中生成，不会写进仓库；测试结束自动清理。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "image_tool.py"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run(*args: object) -> subprocess.CompletedProcess[str]:
    """用当前解释器调用一次命令行入口。"""
    return subprocess.run(
        [sys.executable, str(ENTRY), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", env=ENV,
    )


def main() -> int:
    passed = 0
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        # 造一张 640x480 的彩色测试图，以及一张带透明通道的 PNG
        color = np.zeros((480, 640, 3), np.uint8)
        cv2.rectangle(color, (40, 40), (300, 240), (30, 90, 200), -1)
        cv2.circle(color, (480, 260), 100, (60, 180, 60), -1)
        src = work / "demo.png"
        cv2.imwrite(str(src), color)

        rgba = cv2.cvtColor(color, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = 128
        alpha = work / "alpha.png"
        cv2.imwrite(str(alpha), rgba)
        (work / "not_image.txt").write_text("this is not an image", encoding="utf-8")
        out_dir = work / "output"

        ok_cases: list[tuple[str, list[object], list[str]]] = [
            ("info", ["info", src], ["图片基础信息", "PNG", "640 x 480", "RGB"]),
            ("resize 只给宽", ["resize", src, "-W", 320], ["320 x 240", "已保存"]),
            ("resize 只给高", ["resize", src, "-H", 240], ["320 x 240", "已保存"]),
            ("resize 指定宽高", ["resize", src, "-W", 800, "-H", 600], ["800 x 600", "已保存"]),
            ("crop", ["crop", src, "-b", "10,20,300,240"], ["290 x 220", "已保存"]),
            ("rotate 90", ["rotate", src, "-a", 90], ["480 x 640", "已保存"]),
            ("rotate 180", ["rotate", src, "-a", 180], ["640 x 480", "已保存"]),
            ("rotate 270", ["rotate", src, "-a", 270], ["480 x 640", "已保存"]),
            ("flip 水平", ["flip", src, "-d", "horizontal"], ["翻转完成", "已保存"]),
            ("flip 垂直", ["flip", src, "-d", "vertical"], ["翻转完成", "已保存"]),
            ("grayscale", ["grayscale", src], ["灰度化完成", "已保存"]),
            ("convert PNG->JPG", ["convert", src, "-t", "jpg"], ["已保存"]),
            ("convert RGBA->JPG", ["convert", alpha, "-t", "jpg"], ["已保存"]),
            ("convert PNG->WEBP", ["convert", src, "-t", "webp"], ["已保存"]),
        ]
        for name, argv, keywords in ok_cases:
            result = run(*argv)
            assert result.returncode == 0, f"{name} 退出码 {result.returncode}: {result.stderr}"
            assert all(k in result.stdout for k in keywords), f"{name} 输出不符: {result.stdout}"
            print(f"[OK] {name}")
            passed += 1

        fail_cases: list[tuple[str, list[object], str]] = [
            ("文件不存在", ["info", work / "missing.png"], "文件不存在"),
            ("不是有效图片", ["info", work / "not_image.txt"], "不是有效图片"),
            ("缩放缺参数", ["resize", src], "至少需要指定"),
            ("宽高非正数", ["resize", src, "-W", -5], "大于 0"),
            ("裁剪参数个数", ["crop", src, "-b", "1,2,3"], "4 个整数"),
            ("裁剪坐标非整数", ["crop", src, "-b", "a,b,c,d"], "必须是整数"),
            ("裁剪越界", ["crop", src, "-b", "10,20,9000,240"], "越界"),
            ("裁剪非法区域", ["crop", src, "-b", "300,20,10,240"], "不合法"),
            ("旋转角度不支持", ["rotate", src, "-a", 45], "仅支持"),
            ("输出覆盖原图", ["convert", src, "-t", "png", "-o", src], "不会覆盖原图"),
        ]
        for name, argv, keyword in fail_cases:
            result = run(*argv)
            assert result.returncode == 1, f"{name} 应返回 1，实际 {result.returncode}"
            assert keyword in (result.stdout + result.stderr), f"{name} 提示不符: {result.stderr}"
            print(f"[OK] 错误处理：{name}")
            passed += 1

        # 通用要求：带透明通道的 PNG 存成 JPG 后必须是 3 通道 RGB
        converted = cv2.imread(str(out_dir / "alpha_converted.jpg"), cv2.IMREAD_UNCHANGED)
        assert converted is not None and converted.ndim == 3 and converted.shape[2] == 3, \
            "RGBA 转 JPG 未正确转成 3 通道图像"
        print("[OK] 透明通道处理：RGBA -> JPG 得到 3 通道图像")
        passed += 1

        # 通用要求：编辑过程不能改动原图
        original = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
        assert original is not None and np.array_equal(original, color), "原图被修改了"
        print("[OK] 原图保持不变")
        passed += 1

    print(f"全部通过：{passed} 项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
