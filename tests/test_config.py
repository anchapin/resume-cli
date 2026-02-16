"""Unit tests for Config class."""

from pathlib import Path

import pytest
import yaml

from cli.utils.config import Config


class TestConfigInitialization:
    """Test Config initialization."""

    def test_init_default_config(self):
        """Test Config initializes with default config."""
        config = Config()

        assert config._config is not None
        assert "output" in config._config
        assert "ai" in config._config
        assert "tracking" in config._config
        assert "github" in config._config

    def test_init_with_config_path(self, temp_dir: Path):
        """Test Config loads from file if path provided."""
        config_path = temp_dir / "config.yaml"
        user_config = {"ai": {"model": "gpt-4", "temperature": 0.8}}
        with open(config_path, "w") as f:
            yaml.dump(user_config, f)

        config = Config(config_path)

        assert config.ai_model == "gpt-4"
        assert config.get("ai.temperature") == 0.8

    def test_init_with_nonexistent_path(self, temp_dir: Path):
        """Test Config ignores nonexistent path."""
        config_path = temp_dir / "nonexistent.yaml"
        config = Config(config_path)

        # Should use defaults
        assert config.ai_model == Config.DEFAULT_CONFIG["ai"]["model"]


class TestConfigDeepMerge:
    """Test deep merge functionality."""

    def test_merge_config_simple(self):
        """Test simple config merge."""
        config = Config()
        user_config = {"ai": {"model": "gpt-4"}}
        config._merge_config(user_config)

        assert config.ai_model == "gpt-4"
        # Other defaults should remain
        assert config.fallback_to_template == Config.DEFAULT_CONFIG["ai"]["fallback_to_template"]

    def test_merge_config_nested(self):
        """Test nested config merge."""
        config = Config()
        user_config = {"output": {"directory": "custom_output"}}
        config._merge_config(user_config)

        assert config.output_dir == Path("custom_output")
        # Other output defaults remain
        assert (
            config.get("output.naming_scheme") == Config.DEFAULT_CONFIG["output"]["naming_scheme"]
        )

    def test_merge_config_multiple_sections(self, temp_dir: Path):
        """Test merge with multiple config sections."""
        config = Config()
        user_config = {
            "ai": {"model": "gpt-4"},
            "github": {"username": "customuser"},
            "tracking": {"enabled": False},
        }
        config._merge_config(user_config)

        assert config.ai_model == "gpt-4"
        assert config.github_username == "customuser"
        assert config.tracking_enabled is False

    def test_merge_config_no_override(self):
        """Test merge doesn't override when user config is empty."""
        config = Config()
        original_model = config.ai_model
        config._merge_config({})

        assert config.ai_model == original_model


class TestConfigGet:
    """Test get method."""

    def test_get_top_level_key(self):
        """Test get retrieves top-level config value."""
        config = Config()
        value = config.get("output")

        assert isinstance(value, dict)
        assert "directory" in value

    def test_get_nested_key(self):
        """Test get retrieves nested config value."""
        config = Config()
        value = config.get("ai.model")

        assert value == Config.DEFAULT_CONFIG["ai"]["model"]

    def test_get_with_default(self):
        """Test get returns default value for missing key."""
        config = Config()
        value = config.get("missing.key", "default_value")

        assert value == "default_value"

    def test_get_missing_key_no_default(self):
        """Test get returns None for missing key without default."""
        config = Config()
        value = config.get("missing.key")

        assert value is None

    def test_get_after_merge(self, temp_dir: Path):
        """Test get returns merged values."""
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"ai": {"model": "custom-model"}}, f)

        config = Config(config_path)
        value = config.get("ai.model")

        assert value == "custom-model"


class TestConfigSet:
    """Test set method."""

    def test_set_existing_key(self):
        """Test set updates existing config value."""
        config = Config()
        config.set("ai.model", "new-model")

        assert config.get("ai.model") == "new-model"

    def test_set_new_key(self):
        """Test set creates new nested structure."""
        config = Config()
        config.set("custom.nested.key", "value")

        assert config.get("custom.nested.key") == "value"
        assert "custom" in config._config
        assert "nested" in config._config["custom"]

    def test_set_deep_nested(self):
        """Test set creates deep nested structure."""
        config = Config()
        config.set("level1.level2.level3", "deep_value")

        assert config.get("level1.level2.level3") == "deep_value"


class TestConfigSave:
    """Test save method."""

    def test_save_creates_file(self, temp_dir: Path):
        """Test save creates config file."""
        config_path = temp_dir / "saved_config.yaml"
        config = Config()
        config.set("test.key", "test_value")

        config.save(config_path)

        assert config_path.exists()

        # Load the saved config back into a new Config object
        loaded_config = Config(config_path)
        assert loaded_config.get("test.key") == "test_value"

    def test_save_creates_directories(self, temp_dir: Path):
        """Test save creates parent directories."""
        nested_path = temp_dir / "nested" / "dir" / "config.yaml"
        config = Config()
        config.set("test", "value")

        config.save(nested_path)

        assert nested_path.parent.exists()
        assert nested_path.exists()

    def test_save_without_path_raises_error(self):
        """Test save raises ValueError when no path specified."""
        config = Config()
        config.config_path = None

        with pytest.raises(ValueError) as exc_info:
            config.save()

        assert "No config path specified" in str(exc_info.value)


class TestConfigProperties:
    """Test config properties."""

    def test_output_dir_property(self):
        """Test output_dir property returns Path."""
        config = Config()
        output_dir = config.output_dir

        assert isinstance(output_dir, Path)
        assert str(output_dir) == Config.DEFAULT_CONFIG["output"]["directory"]

    def test_default_variant_property(self):
        """Test default_variant property."""
        config = Config()
        variant = config.default_variant

        assert variant == Config.DEFAULT_CONFIG["generation"]["default_variant"]

    def test_default_format_property(self):
        """Test default_format property."""
        config = Config()
        fmt = config.default_format

        assert fmt == Config.DEFAULT_CONFIG["generation"]["default_format"]

    def test_ai_provider_property(self):
        """Test ai_provider property."""
        config = Config()
        provider = config.ai_provider

        assert provider == Config.DEFAULT_CONFIG["ai"]["provider"]

    def test_ai_model_property(self):
        """Test ai_model property."""
        config = Config()
        model = config.ai_model

        assert model == Config.DEFAULT_CONFIG["ai"]["model"]

    def test_fallback_to_template_property(self):
        """Test fallback_to_template property."""
        config = Config()
        fallback = config.fallback_to_template

        assert fallback == Config.DEFAULT_CONFIG["ai"]["fallback_to_template"]

    def test_tracking_enabled_property(self):
        """Test tracking_enabled property."""
        config = Config()
        enabled = config.tracking_enabled

        assert enabled == Config.DEFAULT_CONFIG["tracking"]["enabled"]

    def test_tracking_csv_path_property(self):
        """Test tracking_csv_path property returns Path."""
        config = Config()
        csv_path = config.tracking_csv_path

        assert isinstance(csv_path, Path)
        assert str(csv_path) == Config.DEFAULT_CONFIG["tracking"]["csv_path"]

    def test_github_username_property(self):
        """Test github_username property."""
        config = Config()
        username = config.github_username

        assert username == Config.DEFAULT_CONFIG["github"]["username"]

    def test_github_sync_months_property(self):
        """Test github_sync_months property."""
        config = Config()
        months = config.github_sync_months

        assert months == Config.DEFAULT_CONFIG["github"]["sync_months"]

    def test_anthropic_base_url_property(self):
        """Test anthropic_base_url property."""
        config = Config()
        url = config.anthropic_base_url

        # Default is empty string, should return None
        assert url is None

    def test_anthropic_base_url_property_with_value(self, temp_dir: Path):
        """Test anthropic_base_url with configured value."""
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"ai": {"anthropic_base_url": "https://custom.api"}}, f)

        config = Config(config_path)
        url = config.anthropic_base_url

        assert url == "https://custom.api"

    def test_openai_base_url_property(self):
        """Test openai_base_url property."""
        config = Config()
        url = config.openai_base_url

        # Default is empty string, should return None
        assert url is None

    def test_openai_base_url_property_with_value(self, temp_dir: Path):
        """Test openai_base_url with configured value."""
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"ai": {"openai_base_url": "https://custom.openai"}}, f)

        config = Config(config_path)
        url = config.openai_base_url

        assert url == "https://custom.openai"

    def test_cover_letter_enabled_property(self):
        """Test cover_letter_enabled property."""
        config = Config()
        enabled = config.cover_letter_enabled

        assert enabled == Config.DEFAULT_CONFIG["cover_letter"]["enabled"]

    def test_cover_letter_formats_property(self):
        """Test cover_letter_formats property."""
        config = Config()
        formats = config.cover_letter_formats

        assert formats == Config.DEFAULT_CONFIG["cover_letter"]["formats"]

    def test_cover_letter_smart_guesses_property(self):
        """Test cover_letter_smart_guesses property."""
        config = Config()
        guesses = config.cover_letter_smart_guesses

        assert guesses == Config.DEFAULT_CONFIG["cover_letter"]["smart_guesses"]

    def test_cover_letter_tone_property(self):
        """Test cover_letter_tone property."""
        config = Config()
        tone = config.cover_letter_tone

        assert tone == Config.DEFAULT_CONFIG["cover_letter"]["tone"]

    def test_cover_letter_max_length_property(self):
        """Test cover_letter_max_length property."""
        config = Config()
        max_len = config.cover_letter_max_length

        assert max_len == Config.DEFAULT_CONFIG["cover_letter"]["max_length"]
