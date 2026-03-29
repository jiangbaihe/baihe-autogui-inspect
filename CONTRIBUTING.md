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
- Python `3.8` is the baseline because it is the last Python release that still runs on Windows 7
- Python `3.8` must stay pinned to `PySide6==6.1.3`, which is the last Qt line this project treats as Win7-safe
- Python `3.9+` may resolve a newer compatible `PySide6`

## Dependency And Workspace Rules

- `baihe-autogui-inspect` depends on `baihe-autogui`
- End users should normally install inspect via `baihe-autogui[inspect]` or `baihe-autogui[extra]`
- Prefer reusing dependencies already declared by `baihe-autogui` instead of duplicating them here
- Only add an inspect-side dependency when it is truly specific to `baihe-autogui-inspect`
- Screen highlight rendering should stay aligned with `baihe-autogui` and reuse its overlay backend when practical
- CI and release validation should resolve `baihe-autogui` from publishable package metadata, not from a checked-out sibling workspace
- When regenerating `uv.lock`, prefer `uv lock --no-sources` so the lockfile does not accidentally capture a local editable sibling checkout
- For local cross-repo debugging against an unreleased `baihe-autogui`, install it explicitly after `uv sync`, for example:

```bash
uv pip install -e ../baihe-autogui --no-deps
```

## Release Order Policy

- `baihe-autogui` must remain independently releasable
- `baihe-autogui-inspect` may depend on a newer published `baihe-autogui`
- If inspect needs a new main-package capability, release `baihe-autogui` first, then release `baihe-autogui-inspect`
- Do not republish `baihe-autogui` just to point at every new inspect patch, as long as the existing `inspect` / `extra` range already covers that compatible release line

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
- Keep the Win7 / Python 3.8 / `PySide6==6.1.3` relationship explicit in both metadata and docs
- Prefer tests that mock GUI state where practical

## Common Commands

```bash
uv sync --dev
uv run pytest -q
uv run ruff check .
uv run mypy src tests
uv run pre-commit run --all-files
uv build
```

Optional local integration override:

```bash
uv pip install -e ../baihe-autogui --no-deps
```

If needed, run the wheel smoke check:

```bash
uv run --python 3.8 --no-project --with ./dist/*.whl python scripts/smoke_import.py
```

## Release Checklist

1. Update code, tests, and docs.
2. Update the version in `pyproject.toml`.
3. Refresh `uv.lock` if the version or dependencies changed.
4. Regenerate `uv.lock` with publishable metadata semantics:

```bash
uv lock --no-sources
```

5. Run local checks on Python 3.8:

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
