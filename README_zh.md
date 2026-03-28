# baihe-autogui-inspect

`baihe-autogui-inspect` 是 `baihe-autogui` 的 Windows GUI 辅助检查工具，用来在编写自动化脚本前查看桌面控件、浏览 UI 树、读取元素属性、辅助定位目标。

这个项目基于此前的 `pyside6-inspect` 演进而来。原始工作由 **Dmitry Vodopyanov** 和 **Alexander Smirnov** 完成，现在它被整理为 Baihe 生态中的独立扩展项目，并依赖 `baihe-autogui`。

## 功能

- 浏览当前运行中的 Windows 应用 UI 树
- 在 `uia`、`win32`、`atspi` 后端之间切换
- 查看当前选中元素的属性
- 直接从桌面点选元素
- 在屏幕上高亮当前选中或悬停的元素
- 显示关键检查操作的耗时
- 同时输出控制台日志和滚动日志文件

## 环境要求

- Windows
- Python >=3.8
- `uv` 或 `pip`

## 安装

本地开发环境推荐使用：

```bash
uv sync
```

或者：

```bash
pip install -e .
```

## 运行

```bash
baihe-inspect
```

或者：

```bash
python -m baihe_autogui_inspect
```

## 日志

默认情况下，程序会在当前工作目录写入 `baihe_autogui_inspect.log`。

可选环境变量：

- `BAIHE_AUTOGUI_INSPECT_LOG_LEVEL`
- `BAIHE_AUTOGUI_INSPECT_LOG_FILE`

示例：

```powershell
$env:BAIHE_AUTOGUI_INSPECT_LOG_LEVEL = "INFO"
$env:BAIHE_AUTOGUI_INSPECT_LOG_FILE = "logs\\inspect.log"
baihe-inspect
```

## 开发

运行测试：

```bash
python -m pytest -q
```

运行 lint 和类型检查：

```bash
python -m ruff check src tests
python -m mypy src tests
```

## 更新记录

版本记录见 [CHANGELOG.md](CHANGELOG.md)。
