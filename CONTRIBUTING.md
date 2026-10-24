# Contributing Guide

Thank you for your interest in the Self-Healing Infrastructure Platform (SHIP).

This document describes the development practices expected when contributing to the project.

## Development Principles

Contributions should prioritize:

- Security and least privilege.
- Reliability and predictable behavior.
- Clear separation of responsibilities.
- Automated testing.
- Useful documentation.
- Small, reviewable changes.

## Before Making Changes

1. Review the project README and relevant architecture documentation.
2. Check the roadmap to understand the current development phase.
3. Identify the intended behavior and acceptance criteria.
4. Consider the security and operational impact of the proposed change.

## Development Workflow

1. Create a focused branch for a substantial feature or fix.
2. Implement a small, coherent change.
3. Add or update tests where appropriate.
4. Run the relevant checks locally.
5. Review the changes for accidental secrets and unrelated modifications.
6. Update the documentation.
7. Commit using a descriptive message.
8. Push the branch and open a pull request when applicable.

For a solo development milestone, changes may be committed directly to `main` when appropriate. Feature branches are encouraged for larger changes.

## Commit Messages

Use concise messages that describe the change.

Examples:

- `docs: define system architecture`
- `feat: add service health monitoring`
- `fix: enforce remediation cooldown`
- `test: add recovery verification cases`
- `ci: add backend test workflow`

## Testing Expectations

Contributions should include relevant tests for new behavior.

In particular:
- Detection rules should be tested against expected and unexpected conditions.
- Remediation policies should reject unauthorized actions.
- Retry limits and cooldowns should be enforced.
- Recovery should be verified through health checks.
- Failure scenarios should not trigger uncontrolled remediation loops.

Tests that stop containers or disrupt networking must run in an isolated environment.

## Security Requirements

- Never commit secrets, credentials, tokens, or private keys.
- Do not introduce unrestricted shell-command execution.
- Treat Docker Engine access as a privileged capability.
- Validate inputs and enforce authorization on the backend.
- Record security-relevant remediation decisions and actions.
- Report potential vulnerabilities privately according to `SECURITY.md`.

## Documentation

Update the relevant documentation whenever a contribution changes the architecture, configuration, security behavior, API, testing process, or operational workflow.

Documentation must distinguish implemented features from planned capabilities.

## Pull Requests

When pull requests are used, they should include:

- A clear description of the change.
- The motivation and expected behavior.
- Relevant test results.
- Documentation updates.
- Known limitations or security considerations.

## Current Project Status

SHIP is under active development. The architecture, toolchain, and contribution process may evolve as implementation progresses.
