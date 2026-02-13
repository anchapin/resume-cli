"""Configuration management for resume CLI."""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for resume CLI."""

    DEFAULT_CONFIG = {
        "output": {
            "directory": "output",
            "naming_scheme": "resume-{variant}-{date}.{ext}",
            "date_format": "%Y-%m-%d"
        },
        "generation": {
            "default_variant": "v1.0.0-base",
            "default_format": "md",
            "max_bullets": 4
        },
        "ai": {
            "provider": "anthropic",  # anthropic or openai
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 4000,
            "fallback_to_template": True,
            "anthropic_base_url": "",
            "openai_base_url": ""
        },
        "tracking": {
            "enabled": True,
            "csv_path": "tracking/resume_experiment.csv"
        },
        "cover_letter": {
            "enabled": True,
            "template": "cover_letter_md.j2",
            "output_directory": "output",
            "formats": ["md", "pdf"],
            "default_questions": ["motivation", "connection"],
            "optional_questions": ["company_alignment", "relocation", "salary"],
            "smart_guesses": True,
            "tone": "professional",
            "max_length": 400
        },
        "github": {
            "username": "anchapin",
            "sync_months": 3
        },
        "variants": {
            "base": "v1.0.0-base",
            "backend": "v1.1.0-backend",
            "ml_ai": "v1.2.0-ml_ai",
            "fullstack": "v1.3.0-fullstack",
            "devops": "v1.4.0-devops",
            "leadership": "v1.5.0-leadership"
        },
        "ats": {
            "enabled": True,
            "scoring": {
                "format_parsing": 20,
                "keywords": 30,
                "section_structure": 20,
                "contact_info": 15,
                "readability": 15
            }
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml. If None, uses default config.
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()

        if config_path and config_path.exists():
            self.load(config_path)

    def load(self, config_path: Path) -> None:
        """Load configuration from file."""
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f) or {}
            self._merge_config(user_config)

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Merge user config with defaults (deep merge)."""
        def deep_merge(base: Dict, update: Dict) -> Dict:
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        self._config = deep_merge(self._config, user_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "ai.model")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key.

        Args:
            key: Dot-notation key
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No config path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    @property
    def output_dir(self) -> Path:
        """Get output directory path."""
        return Path(self.get("output.directory", "output"))

    @property
    def default_variant(self) -> str:
        """Get default variant name."""
        return self.get("generation.default_variant", "v1.0.0-base")

    @property
    def default_format(self) -> str:
        """Get default output format."""
        return self.get("generation.default_format", "md")

    @property
    def ai_provider(self) -> str:
        """Get AI provider name."""
        return self.get("ai.provider", "anthropic")

    @property
    def ai_model(self) -> str:
        """Get AI model name."""
        return self.get("ai.model", "claude-3-5-sonnet-20241022")

    @property
    def fallback_to_template(self) -> bool:
        """Whether to fallback to template on AI failure."""
        return self.get("ai.fallback_to_template", True)

    @property
    def tracking_enabled(self) -> bool:
        """Whether tracking is enabled."""
        return self.get("tracking.enabled", True)

    @property
    def tracking_csv_path(self) -> Path:
        """Get tracking CSV path."""
        return Path(self.get("tracking.csv_path", "tracking/resume_experiment.csv"))

    @property
    def github_username(self) -> str:
        """Get GitHub username."""
        return self.get("github.username", "anchapin")

    @property
    def github_sync_months(self) -> int:
        """Get GitHub sync months."""
        return self.get("github.sync_months", 3)

    @property
    def anthropic_base_url(self) -> Optional[str]:
        """Get Anthropic API base URL (None if not set)."""
        url = self.get("ai.anthropic_base_url", "")
        return url if url else None

    @property
    def openai_base_url(self) -> Optional[str]:
        """Get OpenAI API base URL (None if not set)."""
        url = self.get("ai.openai_base_url", "")
        return url if url else None

    @property
    def cover_letter_enabled(self) -> bool:
        """Whether cover letter generation is enabled."""
        return self.get("cover_letter.enabled", True)

    @property
    def cover_letter_formats(self) -> list:
        """Get cover letter output formats."""
        return self.get("cover_letter.formats", ["md", "pdf"])

    @property
    def cover_letter_smart_guesses(self) -> bool:
        """Whether to use smart guesses in non-interactive mode."""
        return self.get("cover_letter.smart_guesses", True)

    @property
    def cover_letter_tone(self) -> str:
        """Get cover letter tone."""
        return self.get("cover_letter.tone", "professional")

    @property
    def cover_letter_max_length(self) -> int:
        """Get cover letter max length in words."""
        return self.get("cover_letter.max_length", 400)

    @property
    def ats_enabled(self) -> bool:
        """Whether ATS checking is enabled."""
        return self.get("ats.enabled", True)
