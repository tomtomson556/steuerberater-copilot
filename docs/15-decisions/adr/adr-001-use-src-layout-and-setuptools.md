# ADR 001: Use src layout and setuptools packaging

## Status

Accepted

## Context

The repository already uses a Python package under `src/` and keeps tests,
fixtures, tools, and documentation outside the package source tree.

Package metadata and build configuration are defined in `pyproject.toml`. The
current build backend is setuptools, and package discovery is configured for the
`src` directory.

Local development and CI both use an editable development install with the
project's dev dependencies before running the repository checks.

## Decision

The project will continue to use the Python `src/` layout with package
configuration in `pyproject.toml` and setuptools packaging.

The editable development install remains the expected local and CI setup for
the current offline MVP codebase.

This decision documents the existing technical baseline only. It does not
change fachliche runtime logic, tax behavior, review behavior, or workflow
behavior.

## Consequences

The `src/` layout keeps source code clearly separated from tests, synthetic
fixtures, tools, and documentation.

The packaging setup supports later local offline MVP entry points, such as a
CLI or API prototype, without changing the current package boundary.

This decision introduces no productive integration, no real data handling, no
tax advice, and no tax calculation logic.

It remains compatible with the project's offline-only scope, synthetic
fixtures, deterministic workflow, and Human Review requirements.
