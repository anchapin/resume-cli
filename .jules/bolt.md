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

## 2026-07-25 - Redundant Lowercasing in Generator Expressions
**Learning:** In Python, calling methods like `.lower()` on strings inside a comprehension or generator expression that iterates over the same text multiple times (e.g., `[kw for kw in items if kw in text.lower()]`) results in the `.lower()` operation being evaluated repeatedly for every iteration. This causes unnecessary $O(N)$ memory allocations and CPU overhead, especially on large strings.
**Action:** Cache the result of such operations outside the loop or generator expression (e.g., `text_lower = text.lower()`) and use the cached variable inside the comprehension.
