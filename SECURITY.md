# Security Policy

EvalVault strives to provide a secure evaluation experience for everyone. Please follow
this policy when reporting potential vulnerabilities.

## Supported Versions

We release security fixes for the latest minor version on the `main` branch. When a new
tag is published, we announce it in the CHANGELOG. If you require backports for older
versions, reach out before disclosing sensitive details publicly.

## Reporting a Vulnerability

- Email `security@evalvault.dev` with the subject line `SECURITY REPORT`.
- Include detailed reproduction steps, logs, and affected commit/tag hashes.
- If possible, suggest mitigations or a failing test case.
- Allow us at least **14 days** to investigate before disclosing publicly.

We will acknowledge receipt within 48 hours and keep you informed as we triage and fix
the issue. When the fix ships, we will credit reporters who wish to be named.

## Scope

This policy covers all code and assets in this repository, including GitHub Actions
workflows and published packages on PyPI. Please avoid:

- Denial-of-service attacks that may impact shared infrastructure
- Automated scanning that violates hosting provider terms of service
- Accessing accounts or data that you do not own

## Disclosure Process

1. Report privately following the steps above.
2. Collaborate with maintainers on impact assessment and remediation.
3. Coordinate a disclosure date so users can update safely.

Thank you for helping keep EvalVault safe for the community.
