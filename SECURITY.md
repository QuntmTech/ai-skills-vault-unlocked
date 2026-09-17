# Security policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature when enabled. Do not open a
public issue containing a credential, exploit, private path, or sensitive log.

## Repository safety rules

- Credentials and `.env` files are prohibited.
- Collected skill content is never executed by repository validation.
- Contributors must inspect scripts before adding them.
- Security-sensitive changes should receive a focused review before merging.

If a secret is committed, revoke it immediately, remove it from Git history, and
review downstream forks and automation logs.

