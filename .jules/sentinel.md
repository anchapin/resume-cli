## 2025-02-12 - [Critical] API Authentication Fail-Open Default
**Vulnerability:** The API authentication mechanism (`api/auth.py`) defaulted to allowing access if the `RESUME_API_KEY` environment variable was not set ("dev mode"). Additionally, it used a timing-vulnerable string comparison for the API key check.
**Learning:** "Dev mode" defaults that bypass security controls are dangerous because they can easily be deployed to production by accident, leaving the system wide open.
**Prevention:** Implement a "fail-closed" strategy. If a security configuration (like an API key) is missing, the application should refuse to start or deny all requests, rather than failing open. Always use `secrets.compare_digest` for sensitive string comparisons.

## 2025-02-19 - [Critical] LaTeX Injection in Cover Letter Generator
**Vulnerability:** The `CoverLetterGenerator` used a standard Jinja2 environment (intended for HTML/XML or plain text) to render LaTeX templates. This allowed malicious user input (or AI hallucinations) containing LaTeX control characters (e.g., `\input{...}`) to be injected directly into the LaTeX source, leading to potential Local File Inclusion (LFI) or other exploits.
**Learning:** Jinja2's default `autoescape` is context-aware based on file extensions, but usually only for HTML/XML. It does NOT automatically escape LaTeX special characters. Relying on manual filters (like `| latex_escape`) in templates is error-prone and brittle, as developers might forget to apply them to every variable.
**Prevention:** Always use a dedicated Jinja2 environment for LaTeX generation that enforces auto-escaping via a `finalize` hook (e.g., `tex_env.finalize = latex_escape`). This ensures *all* variable output is sanitized by default, providing defense-in-depth even if the template author forgets explicit filters.

## 2026-07-18 - [CRITICAL] LaTeX Command Injection and DoS
**Vulnerability:** PDF compilation commands in `cli/pdf/converter.py` and `cli/generators/cover_letter_generator.py` omitted the `-no-shell-escape` flag, allowing arbitrary command execution via LaTeX `\write18`. Additionally, missing timeouts allowed infinite compilation loops, leading to DoS.
**Learning:** LaTeX compilers evaluate untrusted input and require strict process isolation and timeout bounds. `-no-shell-escape` is mandatory to prevent shell injection, and timeouts are required to prevent resource exhaustion.
**Prevention:** Always include `-no-shell-escape` (or equivalent) when invoking LaTeX engines, and wrap all `subprocess.Popen.communicate()` calls with an explicit `timeout` and rigorous process cleanup.
