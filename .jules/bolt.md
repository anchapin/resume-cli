## 2025-02-18 - Caching Jinja2 Environment
**Learning:** Instantiating Jinja2 Environment is surprisingly expensive (35ms vs 0.7ms) even with FileSystemLoader, likely due to filter registration and internal setup.
**Action:** Cache Environment instances at class level when template directory is constant or keys are manageable.
