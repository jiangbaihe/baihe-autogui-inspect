# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Added Windows GitHub Actions workflows for CI and tag-driven releases.
- Added a wheel smoke import script for release validation.

### Changed

- Relaxed the published runtime requirement to `Python >=3.8` while keeping development and release validation based on Python 3.8.
- Documented the dependency policy that reuses `baihe-autogui` as the primary extension base and keeps local workspace development on sibling repositories.

## [0.1.0] - 2026-03-28

### Added

- Introduced `baihe-autogui-inspect` as a dedicated Windows GUI inspection companion for `baihe-autogui`.
- Added package metadata, script entry point, and local workspace wiring for development alongside `baihe-autogui`.

### Changed

- Migrated the codebase from the earlier `pyside6-inspect` package into the `baihe_autogui_inspect` namespace.
- Renamed the application identity, environment variables, and documentation to match the Baihe ecosystem.
- Declared `baihe-autogui` as a runtime dependency for future integration and aligned the release line to a fresh `0.x` series.
