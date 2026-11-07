# Image Toolbox · 图片信息查看与简单编辑工具

## 1. 项目介绍

### 1.1 这个程序做什么

这是一个用 Python + OpenCV 编写的小工具：读取一张图片的基础信息，并对图片做几种简单编辑。所有编辑结果都另存为新文件，**原图永远不会被改动**。

### 1.2 支持哪些功能

| 类别 | 功能 | 具体说明 |
| --- | --- | --- |
| 读取信息 | `info` | 文件名、图片格式（按文件头识别）、宽度和高度（像素）、颜色模式（RGB / RGBA / 灰度等）、文件大小（KB 或 MB，保留 2 位小数） |
| 编辑 | `resize` 缩放 | 可同时指定宽高；只给宽或只给高时，另一边按原图比例自动计算 |
| 编辑 | `crop` 裁剪 | 指定「左,上,右,下」四个坐标，区域越界时给出明确提示 |
| 编辑 | `rotate` 旋转 | 支持 90 / 180 / 270 度 |
| 编辑 | `flip` 翻转 | 水平翻转 `horizontal`、垂直翻转 `vertical`，另附 `both` 同时翻转 |
| 编辑 | `grayscale` 灰度化 | 彩色图转单通道灰度图 |
| 编辑 | `convert` 格式转换 | PNG 与 JPG 互转，另支持 `bmp`、`webp` |

### 1.3 程序是什么形式

**命令行程序（CLI）**，不需要图形界面，在终端输入命令即可运行。入口是仓库根目录的 `image_tool.py`。

### 1.4 通用约定

1. **不覆盖原图**：不加 `-o` 时，结果自动保存到「原图所在目录 / `output/`」下，文件名为 `原名_操作后缀.扩展名`，并在终端打印保存位置的绝对路径；用 `-o` 指定路径时若与原图相同会被拒绝。
2. **错误提示**：文件不存在、文件不是有效图片、参数不合法（宽高小于等于 0、裁剪越界、角度不支持等）都会打印 `[错误] ...` 并返回退出码 1，不会抛出 Python 堆栈。
3. **透明通道处理**：带 Alpha 通道的 PNG 保存为 JPG 时，先以白底合成并转成 3 通道 RGB，再交给 JPEG 编码器。
4. **代码结构**：按职责拆成 `info.py`（信息）、`edits.py`（编辑）、`utils.py`（读写与异常）、`cli.py`（参数与分发），关键逻辑有简短注释。

## 2. 环境配置

### 2.1 Python 版本

Python **3.10 及以上**（本项目在 Python 3.13 上开发与测试）。

### 2.2 方式 A：使用 uv（推荐）

仓库根目录已提供 `pyproject.toml` 和 `uv.lock`，uv 能一键复现完全一致的依赖版本。

第一步，安装 uv（任选一条）：

```bash
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者已有 Python 时直接用 pip 装
python -m pip install uv
```

第二步，在**仓库根目录**（`README.md` 所在目录）执行：

```bash
uv sync
```

uv 会按 `uv.lock` 创建 `.venv/` 并安装 `opencv-python` 与 `numpy`。之后用 `uv run python image_tool.py ...` 启动程序（见第 3 节）。

### 2.3 方式 B：不使用 uv

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows；macOS / Linux 改为 source .venv/bin/activate
python -m pip install opencv-python numpy
python image_tool.py --help
```

### 2.4 依赖清单

| 依赖 | 版本约束 | 用途 |
| --- | --- | --- |
| `opencv-python` | `>=4.10.0` | 图片读写、缩放、裁剪、旋转、翻转、灰度化、编码 |
| `numpy` | `>=1.26` | 图像数组运算（随 OpenCV 一同安装） |

`.venv/`、`__pycache__/`、`output/` 以及图片文件都由 `.gitignore` 排除，不会被提交。

## 3. 运行方式

### 3.0 启动与查看帮助

在仓库根目录打开终端：

```bash
uv run python image_tool.py --help
```

预期输出：

```text
usage: image_tool.py [-h] 命令 ...

读取图片基础信息并完成简单图片编辑（基于 OpenCV）

positional arguments:
  命令
    info       读取并显示图片基础信息
    resize     缩放图片，只给宽或高时按比例缩放
    crop       裁剪图片，区域为 左,上,右,下
    rotate     旋转图片（90 / 180 / 270 度）
    flip       水平或垂直翻转图片
    grayscale  彩色图转灰度图
    convert    格式转换，例如 PNG 与 JPG 互转

options:
  -h, --help   show this help message and exit
```

准备一张自己的图片，例如把 `demo.png` 放到仓库根目录（仓库不附带图片，避免提交体积过大的文件）。下面的示例都以一张 **640 x 480 的彩色 PNG** 为例，路径用相对路径 `demo.png`。所有编辑命令都支持 `-o/--output` 指定输出路径；不写时自动保存到 `output/` 并打印绝对路径。

### 3.1 读取图片信息

```bash
uv run python image_tool.py info demo.png
```

预期输出：

```text
图片基础信息
------------------------------------------
文件名      demo.png
图片格式    PNG
宽度和高度  640 x 480 像素
颜色模式    RGB（3 通道）
文件大小    4.88 KB
```

### 3.2 缩放 resize

```bash
uv run python image_tool.py resize demo.png --width 320          # 只给宽，按比例算高
uv run python image_tool.py resize demo.png --height 240         # 只给高，按比例算宽
uv run python image_tool.py resize demo.png --width 800 --height 600
uv run python image_tool.py resize demo.png -W 320 -o small.png  # 指定输出文件
```

预期输出：

```text
缩放完成：640 x 480 → 320 x 240 像素
已保存：D:\你的路径\output\demo_resized.png
```

宽高都不给、或有任意一边小于等于 0，会打印 `[错误] ...`。短参数：`-W` 宽、`-H` 高、`-o` 输出。

### 3.3 裁剪 crop

```bash
uv run python image_tool.py crop demo.png --box 10,20,300,240
```

预期输出：

```text
裁剪完成：区域 (10, 20, 300, 240)，结果 290 x 220 像素
已保存：D:\你的路径\output\demo_cropped.png
```

区域越界时的提示：

```bash
uv run python image_tool.py crop demo.png --box 10,20,9000,240
```

```text
[错误] 裁剪区域越界：图片尺寸为 640 x 480 像素，但区域右下角是 (9000, 240)
```

### 3.4 旋转 rotate

```bash
uv run python image_tool.py rotate demo.png --angle 90
uv run python image_tool.py rotate demo.png --angle 180
uv run python image_tool.py rotate demo.png --angle 270
```

预期输出（以 90 度为例，宽高会交换）：

```text
旋转完成：90 度，结果 480 x 640 像素
已保存：D:\你的路径\output\demo_rotated90.png
```

传入 `--angle 45` 会得到 `[错误] 暂不支持 45 度旋转；仅支持 90、180、270 度`。

### 3.5 翻转 flip

```bash
uv run python image_tool.py flip demo.png --direction horizontal   # 水平翻转
uv run python image_tool.py flip demo.png --direction vertical     # 垂直翻转
```

预期输出：

```text
翻转完成：horizontal
已保存：D:\你的路径\output\demo_flipped_horizontal.png
```

`--direction` 可省略，默认 `horizontal`；也支持 `both`（同时水平 + 垂直）。

### 3.6 灰度化 grayscale

```bash
uv run python image_tool.py grayscale demo.png
```

预期输出：

```text
灰度化完成：结果 640 x 480 像素（单通道）
已保存：D:\你的路径\output\demo_grayscale.png
```

### 3.7 格式转换 convert

```bash
uv run python image_tool.py convert demo.png --to jpg     # PNG 转 JPG
uv run python image_tool.py convert photo.jpg --to png    # JPG 转 PNG
uv run python image_tool.py convert demo.png --to webp
```

预期输出：

```text
已保存：D:\你的路径\output\demo_converted.jpg
```

`--to` 可选 `png / jpg / jpeg / bmp / webp`。带透明通道的 PNG 转 JPG 时，程序会先以白底合成再转 3 通道 RGB，不会出现保存失败或黑底：

```bash
uv run python image_tool.py convert alpha.png --to jpg
```

### 3.8 错误提示一览

| 情况 | 示例命令 | 提示 |
| --- | --- | --- |
| 文件不存在 | `... info missing.png` | `[错误] 文件不存在：...` |
| 不是有效图片 | `... info not_image.txt` | `[错误] 文件不是有效图片或该格式不受支持：...` |
| 宽高不合法 | `... resize demo.png -W -5` | `[错误] 宽度必须是大于 0 的整数，收到：-5` |
| 缩放没给参数 | `... resize demo.png` | `[错误] 缩放至少需要指定 --width 或 --height 中的一个` |
| 裁剪坐标格式错 | `... crop demo.png -b 1,2,3` | `[错误] 裁剪区域需要 4 个整数（左,上,右,下）...` |
| 裁剪越界 | `... crop demo.png -b 10,20,9000,240` | `[错误] 裁剪区域越界：图片尺寸为 640 x 480 像素...` |
| 角度不支持 | `... rotate demo.png -a 45` | `[错误] 暂不支持 45 度旋转；仅支持 90、180、270 度` |
| 试图覆盖原图 | `... convert demo.png -t png -o demo.png` | `[错误] 输出路径与原图相同，已拒绝；本程序不会覆盖原图` |

### 3.9 自测

仓库内附一份冒烟测试，会自动生成临时测试图并跑遍全部功能与错误分支：

```bash
uv run python tests/smoke_test.py
```

预期输出（节选）：

```text
[OK] info
[OK] resize 只给宽
...
[OK] 透明通道处理：RGBA -> JPG 得到 3 通道图像
[OK] 原图保持不变
全部通过：26 项
```

## 4. 仓库结构

```text
image-toolbox/
├── .gitignore          排除虚拟环境、缓存、输出图片
├── README.md           本说明文件
├── pyproject.toml      项目元数据与依赖（uv 使用）
├── uv.lock             uv 生成的依赖锁文件
├── image_tool.py       命令行入口
├── image_toolbox/
│   ├── __init__.py
│   ├── __main__.py     支持 python -m image_toolbox
│   ├── cli.py          参数解析与命令分发
│   ├── info.py         图片信息读取
│   ├── edits.py        缩放 / 裁剪 / 旋转 / 翻转 / 灰度化 / 格式映射
│   └── utils.py        图片读写、输出路径、透明通道处理、异常定义
└── tests/
    └── smoke_test.py   冒烟测试
```

## 5. Git 分支与提交

- `main`：初始化提交，以及最终由 `dev` 合并进来的可运行版本。
- `dev`：全部功能开发都在这条分支上进行，提交依次为：读取图片信息 → 缩放与裁剪 → 旋转/翻转/灰度化/格式转换 → 完善 README 与自测。
- 合并方式：`git checkout main` 后执行 `git merge --no-ff dev`，因此 `main` 上直接包含全部最终代码。
