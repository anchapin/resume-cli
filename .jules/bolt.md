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
## 2025-02-18 - Regex Pre-compilation and Hoisting in ATS Generator
**Learning:** Re-compiling regexes and creating large lists/sets (like `_ACTION_VERBS` or `r"\d+%|\$\d+|\d+\s*(users|customers|projects)"`) inside frequently called loops or functions causes unnecessary object creation and compilation overhead. Furthermore, `.lower()` on large strings for entire document parsing just for case-insensitive checks is inefficient and can cause matching bugs (e.g. acronym matching).
**Action:** Always pre-compile regexes and hoist static lists to module-level constants. Use `re.IGNORECASE` when case-insensitive matching is needed instead of eagerly lowercasing the entire large input string if the original case is still required for other patterns.
