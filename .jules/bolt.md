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

## 2025-02-18 - Regex Pre-compilation and `re.IGNORECASE` Overhead in `keyword_density.py`
**Learning:** Pre-compiling `_TITLE_PATTERNS` and `_COMPANY_PATTERNS` at the module level prevents redundant regex compilation overhead on every `generate_report` call. Additionally, the `_count_keywords_in_resume` method suffered from significant overhead due to the `re.IGNORECASE` flag in `re.findall`. Lowercasing the entire resume text once and matching it against lowercased keywords eliminates the need for `re.IGNORECASE`, which provides a substantial performance speedup in the keyword extraction loop without sacrificing accuracy. Combining keywords into a single regex with alternations was intentionally avoided because it fails to properly count overlapping keywords (e.g., 'React' vs 'React Native').
**Action:** When searching for large numbers of keywords case-insensitively, explicitly pre-lowercase both the target text and the search patterns instead of relying on `re.IGNORECASE`. Always pre-compile static regex patterns at the module level.
