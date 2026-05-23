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

## 2024-05-23 - Hoist regex patterns to module scope for ATS Generator
**Learning:** Found that `_check_readability`, `_check_format_parsing`, and keyword extraction dynamically compiled and allocated multiple regular expressions and arrays on every execution. The `_get_all_text` method was converting everything to lowercase too early which created conflict for acronym checks using regex.
**Action:** Pre-compile all regular expressions statically at module level (e.g. `_ACRONYM_PATTERN`, `_TABLE_PATTERN`), hoist arrays like `_ACTION_VERBS` to module level. Removing early string manipulation and using regex flags like `re.IGNORECASE` when case is not needed, or caching `.lower()` strings locally before loop comprehension prevents redundant work per list item.
