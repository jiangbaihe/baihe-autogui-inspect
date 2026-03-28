# baihe-autogui-inspect

`baihe-autogui-inspect` is a Windows GUI inspection companion for `baihe-autogui`. It helps you inspect desktop controls, browse UI trees, view element properties, and locate targets before writing automation scripts.

This project is based on the earlier `pyside6-inspect` work originally developed by **Dmitry Vodopyanov** and **Alexander Smirnov**. It is now packaged as a Baihe ecosystem tool and depends on `baihe-autogui`.

## Features

- Browse the UI tree of running Windows applications
- Switch between `uia`, `win32`, and `atspi` backends
- Inspect properties of the selected element
- Pick an element directly from the desktop
- Highlight the selected or hovered element on screen
- Show timing information for inspection operations
- Write logs to both the console and a rotating log file

## Requirements

- Windows
- Python >=3.8
- `uv` or `pip`

## Installation

For local development:

```bash
uv sync
```

Or:

```bash
pip install -e .
```

## Run

```bash
baihe-inspect
```

Or:

```bash
python -m baihe_autogui_inspect
```

## Logging

By default, the app writes `baihe_autogui_inspect.log` in the current working directory.

Optional environment variables:

- `BAIHE_AUTOGUI_INSPECT_LOG_LEVEL`
- `BAIHE_AUTOGUI_INSPECT_LOG_FILE`

Example:

```powershell
$env:BAIHE_AUTOGUI_INSPECT_LOG_LEVEL = "INFO"
$env:BAIHE_AUTOGUI_INSPECT_LOG_FILE = "logs\\inspect.log"
baihe-inspect
```

## Development

Run tests:

```bash
python -m pytest -q
```

Run lint and type checks:

```bash
python -m ruff check src tests
python -m mypy src tests
```

## Changelog

Release notes are tracked in [CHANGELOG.md](CHANGELOG.md).
