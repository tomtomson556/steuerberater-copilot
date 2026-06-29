# ADR 002: CLI-first offline MVP interface

## Status

Accepted

## Context

The offline MVP is currently local, deterministic, and synthetic.

PR #31 introduced the first usable entry point through a CLI. The CLI returns
JSON output for local inspection, tests, and review.

The project remains without an API server, without UI, without LLM calls, and
without productive integration.

## Decision

The CLI is the first supported entry point for the offline MVP.

JSON output is the primary machine-readable interface in this phase.

FastAPI and other API surfaces are intentionally deferred.

UI surfaces are intentionally deferred.

API or UI work may follow only after a separate decision or ADR and after the
CLI JSON contract is stable enough to guide the next interface.

## Consequences

Local tests and review remain simple.

The offline MVP exposes no network surface.

The security surface remains smaller than an API or UI prototype.

The project does not process productive real data.

Deterministic fixtures make behavior easier to inspect and review.

A later API can orient itself around the CLI JSON contract.

## Non-goals

This decision does not introduce FastAPI implementation.

It does not introduce a UI.

It does not introduce productive integrations.

It does not introduce real data.

It does not introduce tax advice.

It does not introduce tax calculation logic.

It does not introduce automatic filing, submission, or transmission.
