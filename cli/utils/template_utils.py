"""Utility functions for Jinja2 template environment management."""

from datetime import datetime
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .template_filters import latex_escape, proper_title

# Cache for Jinja2 environments to avoid expensive re-initialization
_ENV_CACHE: Dict[str, Environment] = {}


def get_jinja_env(template_dir: Path) -> Environment:
    """
    Get a cached Jinja2 environment for the given template directory.

    Args:
        template_dir: Path to the templates directory.

    Returns:
        A configured Jinja2 Environment instance.
    """
    cache_key = str(template_dir.resolve())

    if cache_key in _ENV_CACHE:
        return _ENV_CACHE[cache_key]

    # Initialize new environment
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add filters
    env.filters["latex_escape"] = latex_escape
    env.filters["proper_title"] = proper_title

    # Add globals
    env.globals["now"] = datetime.now

    # Cache the environment
    _ENV_CACHE[cache_key] = env

    return env
