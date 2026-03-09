## 2025-02-12 - [Critical] API Authentication Fail-Open Default
**Vulnerability:** The API authentication mechanism (`api/auth.py`) defaulted to allowing access if the `RESUME_API_KEY` environment variable was not set ("dev mode"). Additionally, it used a timing-vulnerable string comparison for the API key check.
**Learning:** "Dev mode" defaults that bypass security controls are dangerous because they can easily be deployed to production by accident, leaving the system wide open.
**Prevention:** Implement a "fail-closed" strategy. If a security configuration (like an API key) is missing, the application should refuse to start or deny all requests, rather than failing open. Always use `secrets.compare_digest` for sensitive string comparisons.

## 2025-02-19 - [Critical] LaTeX Injection in Cover Letter Generator
**Vulnerability:** The `CoverLetterGenerator` used a standard Jinja2 environment (intended for HTML/XML or plain text) to render LaTeX templates. This allowed malicious user input (or AI hallucinations) containing LaTeX control characters (e.g., `\input{...}`) to be injected directly into the LaTeX source, leading to potential Local File Inclusion (LFI) or other exploits.
**Learning:** Jinja2's default `autoescape` is context-aware based on file extensions, but usually only for HTML/XML. It does NOT automatically escape LaTeX special characters. Relying on manual filters (like `| latex_escape`) in templates is error-prone and brittle, as developers might forget to apply them to every variable.
**Prevention:** Always use a dedicated Jinja2 environment for LaTeX generation that enforces auto-escaping via a `finalize` hook (e.g., `tex_env.finalize = latex_escape`). This ensures *all* variable output is sanitized by default, providing defense-in-depth even if the template author forgets explicit filters.

## 2024-05-31 - [CRITICAL] Fix command injection vulnerability in pdflatex and pandoc pdf generation
**Vulnerability:** Missing `-no-shell-escape` flag for `pdflatex` compilation, and `--pdf-engine-opt=-no-shell-escape` for `pandoc` compilation.
**Learning:** This codebase compiles LaTeX to PDF using `pdflatex` and `pandoc`. `pdflatex` executes shell commands contained within the LaTeX source files if the `-shell-escape` option is passed, or if it isn't explicitly disabled by `-no-shell-escape`. While standard `pdflatex` sometimes defaults to disabled, explicit disabling is essential, particularly because untrusted input could manipulate the LaTeX template structure.
**Prevention:** Always enforce `-no-shell-escape` parameter explicitly when using `pdflatex` natively and through `pandoc` using `--pdf-engine-opt`.
