# Security Policy

## Scope

This project is a test automation and AI-assisted quality platform intended for internal and commercial use. Security is a core requirement before business deployment.

## Supported versions

This project is currently in a pre-production maturity stage. Security updates are applied to the current main branch and should be reviewed before deployment to production environments.

## Reporting vulnerabilities

Please report suspected security issues privately by emailing the maintainer or through the project’s GitHub security advisory workflow. Do not open public issues for vulnerabilities.

## Security expectations

The following controls are required before production use:

- store secrets in a secret manager, never in source control
- use managed cloud identity and least-privilege access
- enforce HTTPS and secure cookies in deployment
- restrict admin routes and protected APIs
- validate uploaded files and generated payloads
- monitor logs and failed jobs for abnormal behavior
- isolate user/project data by tenant or environment

## Recommendations

- Use Azure Key Vault or AWS Secrets Manager
- Configure RBAC across the platform
- Keep browser automation and API execution isolated in worker pools
- Review AI-generated actions before executing them in sensitive environments
- Add audit logging for test runs, report exports, and admin actions
