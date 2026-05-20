# Security Policy for Kintsugi-DAM

Kintsugi-DAM takes the security and integrity of user data extremely seriously. Because our application is designed to protect digital assets from bit-rot and ransomware, we hold our core architecture to the highest security standards.

## Supported Versions

We currently support the latest major release line. If you are running an older version, we strongly recommend updating to the latest stable Docker image before submitting a report, as your issue may have already been patched.

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 1.x.x   | :white_check_mark: | Active development and security patches. |
| < 1.0   | :x:                | Beta/Legacy versions are no longer supported. |

## Scope of Security Program

**In Scope:**
* **Core Monolith:** Vulnerabilities in the Python FastAPI backend or Next.js frontend (e.g., auth bypass, XSS, CSRF, SQL Injection).
* **The Rust Engine:** Buffer overflows or memory leaks in the PyO3/BLAKE3 hashing engine.
* **Sandbox Escapes:** If you find a way for a 3rd-party community plugin to bypass the `SandboxProxyBus` and execute unauthorized commands (e.g., a plugin requesting `network:outbound` but successfully executing local file deletion).

**Out of Scope:**
* Malicious 3rd-party plugins. (If a user willingly installs a 3rd-party native plugin and ignores the warning prompts, that is a user-configuration risk, not a core vulnerability).
* User misconfiguration (e.g., exposing the Kintsugi-DAM web UI to the public internet without a reverse proxy or strong passwords).
* Denial of Service (DoS) attacks requiring massive external network traffic.

## Reporting a Vulnerability

**DO NOT create a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability within Kintsugi-DAM, please send an e-mail to **[Insert Your Security Email: e.g., security@yourdomain.com]**.

### What to include in your report:
* A descriptive summary of the vulnerability.
* The version of Kintsugi-DAM you are running.
* Step-by-step instructions to reproduce the issue.
* A Proof of Concept (PoC) script or screenshots, if applicable.

### What to expect:
1. **Acknowledgment:** We will acknowledge receipt of your vulnerability report within **48 hours**.
2. **Triage:** We will triage the report and provide an estimated timeline for a fix within **5 business days**.
3. **Resolution:** Once the vulnerability is patched, we will coordinate with you to publish a security advisory. We will gladly provide credit/attribution in our release notes for your responsible disclosure.

*Note: As Kintsugi-DAM is an independent, bootstrapped project, we do not currently offer a paid bug bounty program. However, we deeply appreciate the open-source community's help in keeping our users' data safe.*
