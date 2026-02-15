## 2025-02-04 - API Fail-Open
**Vulnerability:** The API authentication function `get_api_key` was designed to "fail open" (allow access) if the `RESUME_API_KEY` environment variable was not set, assuming a development environment.
**Learning:** Convenience features like "dev mode defaults" can become critical vulnerabilities if they make the system insecure by default in production or misconfigured environments.
**Prevention:** Always "fail closed". Require explicit configuration for security-critical features. If a dev mode is needed, it should be enabled by an explicit flag (e.g., `ALLOW_INSECURE_DEV_MODE=true`), not by the absence of a secret.
