# Contributing

This is the single developer manual for `baihe-autogui-inspect`. It is written to help AI agents continue work quickly, but it should stay readable for human developers too.

## Project Positioning

`baihe-autogui-inspect` is a Windows GUI inspection companion for `baihe-autogui`.

Project priorities:

- Keep the tool practical for real Windows desktop inspection work
- Stay aligned with the `baihe-autogui` ecosystem
- Prefer stable behavior and straightforward packaging

## Python Version Policy

- Published artifacts support `Python >=3.8`
- Local development uses Python `3.8` as the baseline
- Lint, tests, and release validation should be run on Python `3.8`
- When compatibility choices are unclear, prefer the option that keeps Python 3.8 working

## Dependency And Workspace Rules

- `baihe-autogui-inspect` depends on `baihe-autogui`
- Local workspace development uses `tool.uv.sources` to point at `../baihe-autogui`
- Keep the sibling repository layout stable during development
- Do not replace the local editable source with a published dependency during normal iteration
- Prefer reusing dependencies already declared by `baihe-autogui` instead of duplicating them here
- Only add an inspect-side dependency when it is truly specific to `baihe-autogui-inspect`

## Repository Landmarks

- `src/baihe_autogui_inspect/main.py`: process entry point and app bootstrap
- `src/baihe_autogui_inspect/ui/`: main window, overlays, pick mode, and models
- `src/baihe_autogui_inspect/core/`: inspection and worker logic
- `src/baihe_autogui_inspect/utils/logging.py`: logging setup
- `tests/`: regression coverage
- `README.md` / `README_zh.md`: user-facing docs
- `CHANGELOG.md`: version history

## Collaboration Rules

- When user-visible behavior changes, update `README.md`, `README_zh.md`, and `CHANGELOG.md`
- When packaging or runtime policy changes, update this file and `pyproject.toml` together
- Keep Windows-first assumptions explicit; this project is not a cross-platform promise
- Prefer tests that mock GUI state where practical

## Common Commands

```bash
uv sync --dev
uv run pytest -q
uv run ruff check .
uv run mypy src tests
uv build
```

If needed, run the wheel smoke check:

```bash
uv run --python 3.8 --no-project --with ./dist/*.whl python scripts/smoke_import.py
```

## Release Checklist

1. Update code, tests, and docs.
2. Update the version in `pyproject.toml`.
3. Refresh `uv.lock` if the version or dependencies changed.
4. Run local checks on Python 3.8:

```bash
uv sync --dev
uv run pytest -q
uv run ruff check .
uv run mypy src tests
uv build
```

## Local Constraints

- Local development and release validation stay on Python `3.8`
- GitHub Actions test/build jobs run on Windows to match the actual runtime platform
- Smoke import checks should validate the built wheel before release tags are pushed
