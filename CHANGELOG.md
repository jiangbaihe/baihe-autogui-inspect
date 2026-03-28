# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.3] - 2026-03-29

### Fixed

- Split the `PySide6` dependency by interpreter version so Python 3.8 stays pinned to `PySide6==6.1.3` for Win7-oriented compatibility, while Python 3.9 and newer resolve a newer compatible PySide6 automatically.
- Raised the `baihe-autogui` minimum dependency to `0.1.12` so inspect always installs with the published runtime dependencies it relies on.

### Changed

- Refreshed package metadata and contributor documentation so the Win7-oriented Python 3.8 baseline and recommended installation path through `baihe-autogui[inspect]` are described consistently.

## [0.1.2] - 2026-03-29

### Fixed

- Fixed the exported `__version__` value so installed wheels report the package metadata version correctly.
- Updated smoke-test validation to install the sibling `baihe-autogui` dependency from the checked-out workspace during CI and release builds.
- Corrected release artifact upload paths so workflow artifacts are collected from the checked-out subdirectory layout.

## [0.1.1] - 2026-03-28

### Added

- Added Windows GitHub Actions workflows for CI and tag-driven releases.
- Added a wheel smoke import script for release validation.

### Changed

- Relaxed the published runtime requirement to `Python >=3.8` while keeping development and release validation based on Python 3.8.
- Documented the dependency policy that reuses `baihe-autogui` as the primary extension base and keeps local workspace development on sibling repositories.
- Aligned the runtime baseline with `baihe-autogui>=0.1.11`, which now carries the logging and Windows automation dependencies inspect relies on.

## [0.1.0] - 2026-03-28

### Added

- Introduced `baihe-autogui-inspect` as a dedicated Windows GUI inspection companion for `baihe-autogui`.
- Added package metadata, script entry point, and local workspace wiring for development alongside `baihe-autogui`.

### Changed

- Migrated the codebase from the earlier `pyside6-inspect` package into the `baihe_autogui_inspect` namespace.
- Renamed the application identity, environment variables, and documentation to match the Baihe ecosystem.
- Declared `baihe-autogui` as a runtime dependency for future integration and aligned the release line to a fresh `0.x` series.
