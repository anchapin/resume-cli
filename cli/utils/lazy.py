"""Lazy loading utilities for CLI performance."""

from typing import Any


class LazyConsole:
    """Lazy proxy for rich.console.Console to improve startup time."""

    def __init__(self, **kwargs):
        """Initialize lazy console with arguments for Console constructor."""
        self._kwargs = kwargs
        self._console = None

    @property
    def console(self):
        """Get the underlying Console instance, creating it if needed."""
        if self._console is None:
            from rich.console import Console

            self._console = Console(**self._kwargs)
        return self._console

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying Console."""
        return getattr(self.console, name)
