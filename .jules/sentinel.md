## 2025-02-12 - [Critical] API Authentication Fail-Open Default
**Vulnerability:** The API authentication mechanism (`api/auth.py`) defaulted to allowing access if the `RESUME_API_KEY` environment variable was not set ("dev mode"). Additionally, it used a timing-vulnerable string comparison for the API key check.
**Learning:** "Dev mode" defaults that bypass security controls are dangerous because they can easily be deployed to production by accident, leaving the system wide open.
**Prevention:** Implement a "fail-closed" strategy. If a security configuration (like an API key) is missing, the application should refuse to start or deny all requests, rather than failing open. Always use `secrets.compare_digest` for sensitive string comparisons.

## 2025-02-19 - [Critical] LaTeX Injection in Cover Letter Generator
**Vulnerability:** The `CoverLetterGenerator` used a standard Jinja2 environment (intended for HTML/XML or plain text) to render LaTeX templates. This allowed malicious user input (or AI hallucinations) containing LaTeX control characters (e.g., `\input{...}`) to be injected directly into the LaTeX source, leading to potential Local File Inclusion (LFI) or other exploits.
**Learning:** Jinja2's default `autoescape` is context-aware based on file extensions, but usually only for HTML/XML. It does NOT automatically escape LaTeX special characters. Relying on manual filters (like `| latex_escape`) in templates is error-prone and brittle, as developers might forget to apply them to every variable.
**Prevention:** Always use a dedicated Jinja2 environment for LaTeX generation that enforces auto-escaping via a `finalize` hook (e.g., `tex_env.finalize = latex_escape`). This ensures *all* variable output is sanitized by default, providing defense-in-depth even if the template author forgets explicit filters.

## 2025-02-23 - [Critical] pdflatex RCE and DoS in PDF Compilation
**Vulnerability:** Several places in the codebase (e.g. `cli/pdf/converter.py` and `cli/generators/cover_letter_generator.py`) called `pdflatex` or `pandoc` without the `-no-shell-escape` flag or timeouts, allowing for RCE and DoS.
**Learning:** Even fallback or auxiliary PDF compilation tasks need strict sandboxing. The `subprocess.communicate()` function will block indefinitely if a timeout is not specified, enabling DoS attacks via infinite compilation loops in maliciously crafted documents. Additionally, LaTeX allows shell execution by default which allows malicious users to execute arbitrary commands.
**Prevention:** Enforce `-no-shell-escape` and a timeout (e.g., 30s) on all `pdflatex` and `pandoc` calls. Handle `subprocess.TimeoutExpired` properly by killing the process and calling `communicate` again.
