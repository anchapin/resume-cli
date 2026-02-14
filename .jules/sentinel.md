## 2026-02-14 - Secure by Default API Auth
**Vulnerability:** The API allowed unauthenticated access by default if `RESUME_API_KEY` was not set, assuming a development environment. This "fail-open" design could lead to accidental exposure in production.
**Learning:** Convenience for developers (zero-config dev mode) often conflicts with security. Implicit defaults can be dangerous.
**Prevention:** Enforce "Secure by Default". Require explicit configuration for insecure modes (e.g., `RESUME_INSECURE_MODE=true`).
