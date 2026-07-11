# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.x     | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@[your-domain].com**

You should receive a response within 48 hours. If the issue is confirmed, we will:
1. Acknowledge your report within 48 hours
2. Provide an estimated timeline for a fix
3. Notify you when the fix is released
4. Credit you in the security advisory (unless you prefer anonymity)

## Security Practices

This project follows these security standards:

- **Secrets management:** All secrets stored in AWS Secrets Manager; never in code or environment variables
- **Authentication:** JWT tokens via AWS Cognito with 15-minute expiry
- **Authorization:** ABAC (Attribute-Based Access Control) for all data access
- **Encryption:** TLS 1.3 in transit; AES-256 at rest via AWS KMS
- **Dependency scanning:** Automated via Snyk in CI pipeline
- **Input validation:** Pydantic models for all API inputs; prompt injection detection for AI endpoints
- **Audit trail:** All financial data mutations logged to immutable audit ledger

## Scope

The following are in scope for security reports:
- Authentication/authorization bypasses
- Data exposure (PII leaks, unauthorized access)
- Prompt injection attacks on AI endpoints
- Infrastructure misconfiguration (Terraform, IAM)
- Dependency vulnerabilities (critical/high severity)

The following are out of scope:
- Denial of service attacks
- Social engineering
- Physical security
