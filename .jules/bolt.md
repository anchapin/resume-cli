## 2025-02-21 - Lazy Loading Imports for CLI Startup
**Learning:** Top-level imports in Python CLIs, especially those involving templating engines like Jinja2 or heavy frameworks, can significantly impact startup time (even for simple commands like `--help`). Lazy loading these imports inside the commands that actually use them is a simple and effective optimization.
**Action:** Review top-level imports in CLI entry points and move heavy dependencies (Jinja2, pandas, ml libraries) to local imports where possible.
