## 2025-02-18 - Lazy Loading Config
**Learning:** Instantiating `Config` was consuming ~30-70ms due to `import yaml` and file I/O, even for commands that didn't need it (like `init` or `help`).
**Action:** Implemented lazy loading in `Config` class. `_config` is initialized to `None` and loaded only on first access to properties. This reduces startup time for simple commands and defers the cost for others.

## 2025-02-18 - Caching Jinja2 Environment
**Learning:** Instantiating Jinja2 Environment is surprisingly expensive (35ms vs 0.7ms) even with FileSystemLoader, likely due to filter registration and internal setup.
**Action:** Cache Environment instances at class level when template directory is constant or keys are manageable.

## 2024-05-22 - Lazy Imports for CLI Performance
**Learning:** Top-level imports of heavy libraries (like Jinja2) in a CLI entry point slow down all commands, even those that don't use the library (like `--help`).
**Action:** Move heavy imports inside the specific command functions where they are used.

## 2025-02-18 - Regex Pre-compilation in Hot Paths
**Learning:** Re-compiling regexes inside a frequently called function (like `latex_escape` which runs for every string) creates significant overhead. Pre-compiling them at module level yielded a ~3.2x speedup.
**Action:** Always look for regex compilations inside loops or frequently called functions and move them to module level constants.
## 2026-04-08 - Pre-compile Regex Patterns in Hot Paths
**Learning:** Re-compiling regular expressions inside loops or frequently called functions (like 's extraction methods) creates measurable performance overhead. For example, pre-compiling the salary extraction patterns yielded a ~1.7x speedup in local benchmarks.
**Action:** When working on performance, identify regex compilations inside loops or parsing functions and move them to module-level constants (e.g., ). Ensure flags like  and  are preserved in the compiled object.

## 2024-05-22 - Pre-compile Regex Patterns in JobParser
**Learning:** Re-compiling regular expressions inside loops or frequently called parsing methods (like `_extract_salary_from_text` or `_extract_job_type`) creates measurable performance overhead. Pre-compiling them to module-level constants yields significant speedups.
**Action:** Identify regex compilations inside loops or parsing functions and move them to module-level constants (e.g., `_SALARY_PATTERNS = [re.compile(p) for p in [...]]`). Ensure flags like `re.IGNORECASE` are preserved.
