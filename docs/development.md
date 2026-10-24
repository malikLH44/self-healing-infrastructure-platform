# Development Guide

## 1. Purpose

This guide describes the development workflow for the Self-Healing Infrastructure Platform (SHIP).

The project will initially target a local Docker Compose environment. Development instructions will be updated as components and services are implemented.

## 2. Prerequisites

The planned development environment requires:

- Git for version control.
- Docker Engine or Docker Desktop with Docker Compose support.
- Python for backend development.
- Node.js and npm for frontend development.
- A code editor such as Visual Studio Code.

Specific versions will be documented when the initial application environment is established.

## 3. Repository Structure

```text
self-healing-infrastructure-platform/
├── docs/
├── infrastructure/
│   ├── compose/
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
├── tests/
│   └── resilience/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── SECURITY.md
```

Backend and frontend application directories will be introduced when implementation begins.

## 4. Local Environment

The development environment will use Docker Compose to run the platform and its sample services.

Before starting the environment:
1. Install the required tools.
2. Clone the repository.
3. Review the project documentation.
4. Create local configuration from `.env.example` when environment variables are required.
5. Verify that local secrets are excluded from version control.

A Compose configuration and executable startup commands will be added in the corresponding implementation phase.

## 5. Backend Development

The planned backend uses Python and FastAPI.

Development practices:
- Keep monitoring, detection, remediation, verification, and persistence responsibilities modular.
- Validate configuration and API inputs.
- Handle operational failures explicitly.
- Avoid unrestricted command execution.
- Add tests for new behavior and failure cases.
- Document API changes.

The exact dependency manager, formatting tools, and linting rules will be established with the initial backend implementation.

## 6. Frontend Development

The planned dashboard uses React, TypeScript, and Vite.

Development practices:
- Keep UI components focused on clear responsibilities.
- Display service state and incident lifecycle information consistently.
- Handle API errors and unavailable services gracefully.
- Enforce access control on the backend rather than relying on UI restrictions.
- Avoid exposing secrets or internal diagnostic information unnecessarily.

Frontend setup and test commands will be documented when the application is initialized.

## 7. Testing Strategy

Testing will be introduced incrementally.

### Unit Tests
Validate individual functions and components, including detection rules, policy evaluation, retry limits, and recovery calculations.

### Integration Tests
Validate interactions between the API, persistence layer, monitoring components, and remediation worker.

### Resilience Tests
Inject controlled failures into sample services and verify detection, remediation decisions, recovery outcomes, and recorded metrics.

### Security Tests
Check authorization, configuration handling, rejected actions, and protection against uncontrolled remediation loops.

Tests that intentionally stop services or disrupt network connectivity must run only in an isolated test environment.

## 8. Git Workflow

Each implementation milestone should follow this process:

1. Define the feature and its acceptance criteria.
2. Implement a small, coherent change.
3. Run the relevant tests.
4. Inspect the changes and check for accidental secrets.
5. Update documentation.
6. Review the Git diff.
7. Commit with a descriptive message.
8. Push the completed milestone to GitHub.

Example commands:

```bash
git status
git diff --check
git diff
git add <specific-files>
git commit -m "Add service health monitoring"
git push origin main
```

The example commit message is illustrative; use a message that accurately describes the completed work. Prefer adding specific files rather than staging everything blindly.

## 9. Configuration and Secrets

- Use `.env.example` to document required configuration variables with safe placeholder values.
- Keep actual credentials in local, ignored configuration files or an appropriate secret manager.
- Never commit passwords, API keys, private keys, or access tokens.
- Validate required configuration before starting application components.

## 10. Documentation

Update the relevant documentation when a change affects:
- Architecture or component responsibilities.
- Configuration or installation.
- API behavior.
- Security assumptions.
- Monitoring and remediation policies.
- Testing procedures or measured results.

Document implemented behavior separately from planned features.

## 11. Definition of Done

A feature is considered complete when:
- Its acceptance criteria are satisfied.
- Relevant tests pass.
- Error handling and security implications have been reviewed.
- Documentation reflects the actual behavior.
- The Git changes have been reviewed.
- The milestone has been committed and pushed to GitHub.