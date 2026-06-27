# Release Governance Guide

## Scope

This guide defines release and pull request governance for the current
compliance-first project phase. The current phase is not a productive release
phase, and productive releases are out of scope.

Release governance must preserve the project principle:

```text
KI bereitet vor.
Die Kanzlei prüft.
Der Steuerberater entscheidet.
```

## Pull Request Governance

- Development happens only through small, reviewable pull requests.
- Direct pushes to `main` are not allowed.
- `main` remains protected.
- Agents may prepare branches and pull requests, but must not merge them.
- Merge is performed only by the user in the terminal.
- Squash merge is the standard merge method.
- CI must be green before merge.
- Required Status Check remains binding.
- Human Review remains the fachliche project rule.

## Current Release Boundaries

The current phase does not allow:

- productive releases
- productive integrations
- real data
- tax advice
- tax calculation logic
- weakening existing project principles or policies

These boundaries also exclude productive Agenda, DATEV, ELSTER, banking,
email, cloud, or external API integrations.

## Policy Compatibility

Release governance must remain compatible with:

- Legal Boundaries and StBerG Safety
- Privacy Gateway Contract
- Human Review Layer Policy
- Internal Risk Classification Policy
- Security Baseline Policy
- AI Transparency and AI Act Readiness
- Offline MVP Operations Guide

No release or merge process may bypass the controls, review duties, data
boundaries, or non-production scope described in those documents.
