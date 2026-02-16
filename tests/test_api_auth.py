"""Unit tests for API authentication."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.auth import API_KEY_NAME, api_key_header, get_api_key


class TestGetApiKey:
    """Test get_api_key function."""

    def test_get_api_key_no_env_key_raises_error(self):
        """Test get_api_key raises error when no env key set (fail secure)."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_api_key("provided-key")

            assert exc_info.value.status_code == 500
            assert "configured" in exc_info.value.detail.lower()

    @patch.dict(os.environ, {"RESUME_API_KEY": "secret-key"})
    def test_get_api_key_matches_env_key(self):
        """Test get_api_key validates key against env var."""
        result = get_api_key("secret-key")

        assert result == "secret-key"

    @patch.dict(os.environ, {"RESUME_API_KEY": "secret-key"})
    def test_get_api_key_wrong_key_raises_error(self):
        """Test get_api_key raises error for wrong key."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("wrong-key")

        assert exc_info.value.status_code == 403
        assert "validate credentials" in exc_info.value.detail.lower()

    @patch.dict(os.environ, {"RESUME_API_KEY": "secret-key"})
    def test_get_api_key_none_key_raises_error(self):
        """Test get_api_key raises error for None key."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key(None)

        assert exc_info.value.status_code == 403

    @patch.dict(os.environ, {"RESUME_API_KEY": "secret-key"})
    def test_get_api_key_empty_string_key_raises_error(self):
        """Test get_api_key raises error for empty key."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("")

        assert exc_info.value.status_code == 403

    @patch.dict(os.environ, {"RESUME_API_KEY": "  secret  "})
    @patch.dict(os.environ, {"RESUME_API_KEY": "secret"})
    def test_get_api_key_whitespace_key_trims(self):
        """Test get_api_key does not trim whitespace (should fail)."""
        # Note: APIKeyHeader does not trim, so spaces cause validation failure
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("  secret  ")

        assert exc_info.value.status_code == 403

    @patch.dict(os.environ, {"RESUME_API_KEY": "multi-part-key-with-special-chars!@#$%"})
    def test_get_api_key_special_characters(self):
        """Test get_api_key handles keys with special characters."""
        result = get_api_key("multi-part-key-with-special-chars!@#$%")

        assert result == "multi-part-key-with-special-chars!@#$%"

    @patch.dict(os.environ, {"RESUME_API_KEY": "exact-match-12345"})
    def test_get_api_key_exact_match(self):
        """Test get_api_key accepts exact match."""
        result = get_api_key("exact-match-12345")

        assert result == "exact-match-12345"

    @patch.dict(os.environ, {"RESUME_API_KEY": "SECRET_KEY"})
    def test_get_api_key_case_sensitive(self):
        """Test get_api_key comparison is case-sensitive."""
        # lowercase vs uppercase
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("secret_key")

        assert exc_info.value.status_code == 403


class TestApiKeyHeader:
    """Test API key header configuration."""

    def test_api_key_header_name(self):
        """Test API_KEY_NAME constant."""
        assert API_KEY_NAME == "X-API-KEY"

    def test_api_key_header_type(self):
        """Test api_key_header is properly configured."""
        assert api_key_header is not None
        assert api_key_header.model.name == API_KEY_NAME
        assert api_key_header.auto_error is False


class TestAuthenticationBehavior:
    """Test authentication edge cases and behaviors."""

    @patch.dict(os.environ, {"RESUME_API_KEY": "test-key"})
    def test_repeated_validation_with_same_key(self):
        """Test that same key validates consistently."""
        result1 = get_api_key("test-key")
        result2 = get_api_key("test-key")

        assert result1 == result2 == "test-key"

    @patch.dict(os.environ, {"RESUME_API_KEY": ""})
    def test_empty_env_string_raises_error(self):
        """Test empty env string raises error (fail secure)."""
        # Empty string is falsy, so should behave like no key set
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("any-key")

        assert exc_info.value.status_code == 500
        assert "configured" in exc_info.value.detail.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_no_env_variable_raises_error(self):
        """Test missing env variable raises error (fail secure)."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("any-key")

        assert exc_info.value.status_code == 500
        assert "configured" in exc_info.value.detail.lower()

    @patch.dict(os.environ, {"RESUME_API_KEY": "secret-key-12345"})
    def test_numeric_suffix_key(self):
        """Test key with numeric suffix."""
        result = get_api_key("secret-key-12345")

        assert result == "secret-key-12345"

    @patch.dict(os.environ, {"RESUME_API_KEY": "with-dashes_and_underscores"})
    def test_key_with_dashes_and_underscores(self):
        """Test key with dashes and underscores."""
        result = get_api_key("with-dashes_and_underscores")

        assert result == "with-dashes_and_underscores"

    @patch.dict(os.environ, {"RESUME_API_KEY": "UPPERCASE_KEY"})
    def test_all_uppercase_key(self):
        """Test uppercase key matches uppercase env var."""
        result = get_api_key("UPPERCASE_KEY")

        assert result == "UPPERCASE_KEY"

    @patch.dict(os.environ, {"RESUME_API_KEY": "lowercase_key"})
    def test_lowercase_key_matches_lowercase(self):
        """Test lowercase key matches lowercase env var."""
        result = get_api_key("lowercase_key")

        assert result == "lowercase_key"

    @patch.dict(os.environ, {"RESUME_API_KEY": "MiXeD_CaSe_KeY"})
    def test_mixed_case_key(self):
        """Test mixed case key requires exact match."""
        result = get_api_key("MiXeD_CaSe_KeY")

        assert result == "MiXeD_CaSe_KeY"

    @patch.dict(os.environ, {"RESUME_API_KEY": "  spaces  "})
    def test_env_var_with_spaces_is_not_trimmed(self):
        """Test env var with spaces requires exact match."""
        # The env var keeps the spaces, so "spaces" won't match "  spaces  "
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("spaces")

        assert exc_info.value.status_code == 403
