# Project Roadmap

## Project Strategy

SHIP will be developed incrementally, starting with a secure and testable Docker Compose deployment before expanding toward Kubernetes.

Each phase should deliver a working, verifiable result before the next phase begins. Features will be added only when their requirements, tests, and security implications are understood.

## Phase 1 — Foundation and Design

**Goal:** Establish the project's structure, architecture, security principles, and development workflow.

Planned tasks:
- Document the system architecture and component responsibilities.
- Define incident lifecycle states and remediation policy requirements.
- Establish coding conventions and repository organization.
- Configure environment variables and secret-handling practices.
- Define testing and continuous integration requirements.

**Completion criteria:**
- Initial documentation is consistent.
- The repository structure is established.
- Security assumptions and development procedures are documented.

## Phase 2 — Docker Compose Environment

**Goal:** Create a reproducible local environment for development and testing.

Planned tasks:
- Configure Docker Compose.
- Create sample services with appropriate health checks.
- Define service configuration and resource limits.
- Establish configuration validation and startup procedures.

**Completion criteria:**
- The environment starts reliably.
- Sample services can be monitored.
- Service failures can be reproduced in a controlled manner.

## Phase 3 — Monitoring and Incident Detection

**Goal:** Detect operational failures and persist incident information.

Planned tasks:
- Collect container status and health-check results.
- Add configurable monitoring intervals and timeouts.
- Implement detection rules for service failures.
- Introduce selected CPU, memory, and network checks.
- Record incident lifecycle events in PostgreSQL.
- Handle duplicate events and transient failures.

**Completion criteria:**
- Supported incident types are detected in automated tests.
- Incident records contain relevant timestamps and diagnostic information.
- Transient failures do not cause uncontrolled incident creation.

## Phase 4 — Controlled Remediation

**Goal:** Implement safe, policy-driven recovery actions.

Planned tasks:
- Define and validate remediation policies.
- Implement a restricted set of permitted actions.
- Enforce retry limits, cooldowns, and action timeouts.
- Prevent overlapping remediation attempts.
- Verify recovery using service health checks.
- Record action outcomes and escalate unresolved incidents.

**Completion criteria:**
- Authorized actions execute as expected.
- Unauthorized actions are rejected.
- Failed recovery attempts are recorded accurately.
- Repeated failures cannot trigger an unlimited remediation loop.

## Phase 5 — Web Dashboard and Platform Security

**Goal:** Provide a usable interface for operating and inspecting the platform.

Planned tasks:
- Implement the FastAPI endpoints required by the dashboard.
- Build a React and TypeScript interface.
- Display service status, incidents, remediation history, and recovery outcomes.
- Add backend-enforced authentication and authorization.
- Maintain audit records for sensitive operations.
- Validate API inputs and protect sensitive configuration.

**Completion criteria:**
- Users can inspect platform status and incident history.
- Protected operations require appropriate authorization.
- Remediation decisions and actions can be audited.

## Phase 6 — Automated Resilience Testing

**Goal:** Measure the effectiveness and limitations of automated recovery.

Planned tasks:
- Build repeatable failure-injection tests.
- Test service termination and health-check failures.
- Test selected resource and network failure scenarios.
- Measure detection time, recovery time, and recovery success rate.
- Test retry limits, cooldowns, and failed-remediation behavior.
- Integrate suitable tests into continuous integration.

**Completion criteria:**
- Failure scenarios produce reproducible results.
- Recovery metrics use documented definitions.
- Tests verify both successful recovery and safe failure handling.

## Phase 7 — Observability and CI/CD

**Goal:** Improve operational visibility and development reliability.

Planned tasks:
- Integrate Prometheus metrics.
- Add Grafana dashboards.
- Aggregate relevant logs with Loki.
- Correlate monitoring events, incidents, and remediation actions.
- Configure GitHub Actions for linting, testing, and build validation.
- Add dependency and container-image security checks where appropriate.

**Completion criteria:**
- Important platform behavior is observable.
- Automated checks run on proposed changes.
- Failures can be investigated using correlated logs and metrics.

## Phase 8 — Kubernetes Extension

**Goal:** Evaluate SHIP in a cloud-native orchestration environment.

Planned tasks:
- Deploy sample services to Kubernetes.
- Configure probes, resource requests, and resource limits.
- Adapt monitoring and remediation integrations.
- Apply least-privilege access controls.
- Compare SHIP's remediation behavior with Kubernetes-native recovery.
- Document deployment and operational trade-offs.

**Completion criteria:**
- The platform can be evaluated in a documented Kubernetes environment.
- Native orchestration behavior is distinguished from SHIP-specific actions.
- The security and reliability implications are documented.

## Development Workflow

Each implementation milestone follows the same workflow:

1. Define the scope and acceptance criteria.
2. Implement one coherent feature.
3. Run relevant tests and inspect the results.
4. Update documentation.
5. Review the changes and security implications.
6. Commit and push the completed milestone to GitHub.

A milestone is considered complete only when its expected behavior has been verified.

## Scope Management

The first release prioritizes reliable service monitoring, controlled remediation, incident history, a basic dashboard, and automated resilience tests.

Advanced observability, broader remediation policies, and Kubernetes support follow after the core workflow is stable.

The roadmap may evolve as implementation results reveal new requirements or constraints.