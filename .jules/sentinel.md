## 2025-02-12 - [Critical] API Authentication Fail-Open Default
**Vulnerability:** The API authentication mechanism (`api/auth.py`) defaulted to allowing access if the `RESUME_API_KEY` environment variable was not set ("dev mode"). Additionally, it used a timing-vulnerable string comparison for the API key check.
**Learning:** "Dev mode" defaults that bypass security controls are dangerous because they can easily be deployed to production by accident, leaving the system wide open.
**Prevention:** Implement a "fail-closed" strategy. If a security configuration (like an API key) is missing, the application should refuse to start or deny all requests, rather than failing open. Always use `secrets.compare_digest` for sensitive string comparisons.

## 2025-02-19 - [Critical] LaTeX Injection in Cover Letter Generator
**Vulnerability:** The `CoverLetterGenerator` used a standard Jinja2 environment (intended for HTML/XML or plain text) to render LaTeX templates. This allowed malicious user input (or AI hallucinations) containing LaTeX control characters (e.g., `\input{...}`) to be injected directly into the LaTeX source, leading to potential Local File Inclusion (LFI) or other exploits.
**Learning:** Jinja2's default `autoescape` is context-aware based on file extensions, but usually only for HTML/XML. It does NOT automatically escape LaTeX special characters. Relying on manual filters (like `| latex_escape`) in templates is error-prone and brittle, as developers might forget to apply them to every variable.
**Prevention:** Always use a dedicated Jinja2 environment for LaTeX generation that enforces auto-escaping via a `finalize` hook (e.g., `tex_env.finalize = latex_escape`). This ensures *all* variable output is sanitized by default, providing defense-in-depth even if the template author forgets explicit filters.

## 2025-02-21 - [Critical] RCE and DoS via PDF Compilation
**Vulnerability:** The application executed LaTeX compilation commands (`pdflatex` and `pandoc` via `subprocess.Popen`) without restricting shell escapes (`-no-shell-escape`) and without enforcing a timeout. This allowed malicious LaTeX code (e.g., via `\write18`) to execute arbitrary commands (RCE) and could cause infinite compilation loops (DoS).
**Learning:** Default LaTeX installations often permit limited shell execution or can be tricked into full execution. Additionally, untrusted LaTeX can easily create infinite loops that lock up server resources.
**Prevention:** Always explicitly disable shell escapes during LaTeX compilation (`-no-shell-escape` for pdflatex, `--pdf-engine-opt=-no-shell-escape` for pandoc). Always wrap subprocess calls handling user-supplied data in strict timeouts (e.g., `process.communicate(timeout=30)`) and explicitly kill the process if it times out.
