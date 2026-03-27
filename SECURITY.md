# Security Policy

## Supported Versions

Security fixes are applied to the latest code on `main` and the latest published container image tag.

## Reporting a Vulnerability

Do not open public GitHub issues for suspected vulnerabilities.

Report security issues privately to the repository maintainers through GitHub security advisories or direct maintainer contact. Include:

- affected version or image tag
- impact summary
- reproduction steps
- suggested mitigation, if known

We will acknowledge receipt, validate the report, and coordinate a fix and disclosure plan.

## Scope Notes

This repository publishes software intended to manage self-hosted GitHub Actions runners. Public repositories should not route untrusted workflow code to privileged or host-sensitive runner environments.
