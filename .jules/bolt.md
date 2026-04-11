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
## 2025-02-18 - Pre-lowercasing vs re.IGNORECASE
**Learning:** Benchmarked counting occurrences of keywords in text using  vs pre-lowercasing the text and keywords (both with and without compiled patterns). In Python, for this specific use case, the performance difference was negligible (speedup was ~1.0x to 1.07x). It is not worth replacing  with pre-lowercasing if it adds complexity.
**Action:** Focus on hoisting regex compilation out of loops ( at the module level) rather than manual lowercasing, as / already handles case-insensitivity efficiently.
## 2025-02-18 - Pre-lowercasing vs re.IGNORECASE
**Learning:** Benchmarked counting occurrences of keywords in text using `re.IGNORECASE` vs pre-lowercasing the text and keywords. In Python, for this specific use case, the performance difference was negligible (speedup was ~1.0x to 1.07x). It is not worth replacing `re.IGNORECASE` with pre-lowercasing if it adds complexity.
**Action:** Focus on hoisting regex compilation out of loops (`re.compile()` at the module level) rather than manual lowercasing, as `re.search()`/`re.findall()` already handles case-insensitivity efficiently.
