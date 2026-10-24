# Security Policy

## Project Status

The Self-Healing Infrastructure Platform (SHIP) is under active development and is not yet intended for production use.

Security practices and supported deployment configurations will evolve as the project matures.

## Reporting a Vulnerability

If you discover a potential security vulnerability, please report it responsibly.

Until a dedicated private reporting channel is established, contact the repository maintainer privately through GitHub rather than publishing exploitable details in a public issue.

Please include:
- A description of the potential vulnerability.
- The affected component or configuration.
- Steps to reproduce the issue, where safe and practical.
- The potential security impact.
- Any suggested mitigation, if known.

Do not include real credentials, personal data, or other sensitive information in the report.

## Scope

Security reports may concern:
- Authentication and authorization weaknesses.
- Unauthorized remediation actions.
- Unsafe container-engine access.
- Secret or credential exposure.
- API input-validation issues.
- Uncontrolled remediation loops or denial-of-service risks.
- Insecure deployment configurations.

## Response Process

The maintainer will review the report, assess its severity, and determine appropriate mitigation steps.

Please allow reasonable time for investigation before publicly disclosing an unpatched vulnerability.

## Responsible Testing

Only test SHIP deployments and systems for which you have explicit authorization. Do not disrupt third-party services or access data that does not belong to you.

## Supported Versions

No production-ready release is currently available. Security support expectations for released versions will be defined when release management is established.