"""Unit tests for cli/main.py using CliRunner for proper coverage."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli.main import cli

# Sample minimal resume.yaml for testing - must have all required fields
SAMPLE_YAML_CONTENT = """\
contact:
  name: Test User
  email: test@example.com
  phone: "555-123-4567"
  location: Test City, ST
  url: https://example.com

professional_summary:
  base: |
    Experienced software engineer with 5+ years of experience.
  variants:
    v1.1.0-backend:
      summary_key: backend
    v1.1.0-ml_ai:
      summary_key: ml_ai

experience:
  - company: Test Corp
    title: Software Engineer
    start_date: "2020-01"
    end_date: null
    location: Test City, ST
    bullets:
      - text: Developed APIs using Python and FastAPI
        skills: [Python, FastAPI]
      - text: Managed PostgreSQL databases
        skills: [PostgreSQL]

education:
  - institution: Test University
    degree: BS Computer Science
    start_date: "2016-09"
    end_date: "2020-05"
    location: Test City, ST

skills:
  programming:
    - Python
    - JavaScript
  frameworks:
    - FastAPI
    - React

variants:
  v1.0.0-base:
    description: Base resume
    summary_key: base
    skill_sections: [programming, frameworks]
    max_bullets_per_job: 5
  v1.1.0-backend:
    description: Backend engineer variant
    summary_key: backend
    skill_sections: [programming, frameworks]
    max_bullets_per_job: 3
    emphasize_keywords: [Python, FastAPI, PostgreSQL, API]
  v1.1.0-ml_ai:
    description: ML/AI engineer variant
    summary_key: ml_ai
    skill_sections: [programming, ml_ai]
    max_bullets_per_job: 3

projects:
  featured:
    - name: test-project
      description: A test project
      url: https://github.com/test/test-project
      language: Python
"""


@pytest.fixture
def temp_yaml_file(tmp_path):
    """Create a temporary resume.yaml file for testing."""
    yaml_path = tmp_path / "resume.yaml"
    yaml_path.write_text(SAMPLE_YAML_CONTENT)
    return yaml_path


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""\
output:
  directory: output

tracking:
  enabled: true
  csv_path: tracking/test.csv

github:
  username: testuser

ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  fallback_to_template: true
""")
    return config_path


@pytest.fixture
def runner():
    """Create a Click CliRunner for testing."""
    return CliRunner()


class TestCLIInit:
    """Tests for init command."""

    def test_init_without_existing(self, runner, tmp_path, monkeypatch):
        """Test init command without --from-existing flag."""
        # Mock the yaml path to not exist
        with patch("cli.main.DEFAULT_YAML_PATH", tmp_path / "resume.yaml"):
            result = runner.invoke(cli, ["init"], catch_exceptions=False)

        # Should show message about creating minimal yaml
        assert "resume.yaml" in result.output or "Creating" in result.output

    def test_init_with_existing_file_exists(self, runner, temp_yaml_file, tmp_path, monkeypatch):
        """Test init command when resume.yaml already exists."""
        with patch("cli.main.DEFAULT_YAML_PATH", temp_yaml_file):
            result = runner.invoke(cli, ["init"], catch_exceptions=False)

        # Should show message that file exists
        assert "already exists" in result.output.lower() or result.exit_code == 0


class TestCLIValidate:
    """Tests for validate command."""

    def test_validate_missing_file(self, runner, tmp_path):
        """Test validate command with missing YAML file."""
        result = runner.invoke(
            cli,
            ["--yaml-path", str(tmp_path / "nonexistent.yaml"), "validate"],
            catch_exceptions=False,
        )

        # Should fail with error about missing file
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Error" in result.output


class TestCLIVariants:
    """Tests for variants command."""

    def test_variants_list(self, runner, temp_yaml_file):
        """Test variants command lists variants."""
        result = runner.invoke(
            cli,
            ["--yaml-path", str(temp_yaml_file), "variants"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "v1.0.0-base" in result.output
        assert "v1.1.0-backend" in result.output


class TestCLIGenerate:
    """Tests for generate command."""

    def test_generate_missing_yaml(self, runner, tmp_path):
        """Test generate command with missing YAML."""
        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(tmp_path / "nonexistent.yaml"),
                "generate",
                "-v",
                "v1.0.0-base",
                "-f",
                "md",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestCLIGeneratePackage:
    """Tests for generate-package command."""

    def test_generate_package_missing_job_desc(self, runner, temp_yaml_file):
        """Test generate-package without job description fails."""
        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "generate-package",
            ],
            catch_exceptions=False,
        )

        # Should fail due to missing required option
        assert result.exit_code != 0


class TestCLIApply:
    """Tests for apply command."""

    def test_apply_with_tracking_disabled(self, runner, temp_yaml_file, temp_config_file):
        """Test apply command with tracking disabled."""
        # Create config with tracking disabled
        config_path = temp_config_file
        config_path.write_text("""\
tracking:
  enabled: false
""")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "--config-path",
                str(config_path),
                "apply",
                "TestCompany",
                "applied",
            ],
            catch_exceptions=False,
        )

        # Should exit gracefully with disabled message
        assert "disabled" in result.output.lower() or result.exit_code == 0


class TestCLIAnalyze:
    """Tests for analyze command."""

    def test_analyze_with_tracking_disabled(self, runner, temp_yaml_file, temp_config_file):
        """Test analyze command with tracking disabled."""
        config_path = temp_config_file
        config_path.write_text("""\
tracking:
  enabled: false
""")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "--config-path",
                str(config_path),
                "analyze",
            ],
            catch_exceptions=False,
        )

        assert "disabled" in result.output.lower() or result.exit_code == 0

    def test_analyze_with_no_data(self, runner, temp_yaml_file, tmp_path):
        """Test analyze command with no tracking data."""
        # Create config with tracking to a non-existent file
        config_path = tmp_path / "config.yaml"
        config_path.write_text(f"""\
tracking:
  enabled: true
  csv_path: {tmp_path / "nonexistent.csv"}
""")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "--config-path",
                str(config_path),
                "analyze",
            ],
            catch_exceptions=False,
        )

        # Should handle missing data gracefully
        assert (
            "No tracking data" in result.output or "Error" in result.output or result.exit_code == 0
        )


class TestCLIATSCheck:
    """Tests for ats-check command."""

    def test_ats_check_missing_job_desc(self, runner, temp_yaml_file):
        """Test ats-check without job description fails."""
        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "ats-check",
                "-v",
                "v1.0.0-base",
            ],
            catch_exceptions=False,
        )

        # Should fail due to missing required option
        assert result.exit_code == 2

    def test_ats_check_with_job_desc(self, runner, temp_yaml_file, tmp_path):
        """Test ats-check with job description."""
        job_desc = tmp_path / "job.txt"
        job_desc.write_text("Senior Python Engineer - FastAPI, PostgreSQL")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "ats-check",
                "-v",
                "v1.0.0-base",
                "--job-desc",
                str(job_desc),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "ATS" in result.output or "Score" in result.output

    def test_ats_check_missing_yaml(self, runner, tmp_path):
        """Test ats-check with missing YAML file."""
        job_desc = tmp_path / "job.txt"
        job_desc.write_text("Test job")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(tmp_path / "nonexistent.yaml"),
                "ats-check",
                "-v",
                "v1.0.0-base",
                "--job-desc",
                str(job_desc),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestCLIDiff:
    """Tests for diff command."""

    def test_diff_invalid_variant(self, runner, temp_yaml_file):
        """Test diff command with invalid variant."""
        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "diff",
                "nonexistent-variant",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestCLIKeywordAnalysis:
    """Tests for keyword-analysis command."""

    def test_keyword_analysis_missing_job_desc(self, runner, temp_yaml_file):
        """Test keyword-analysis without job description fails."""
        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "keyword-analysis",
                "-v",
                "v1.0.0-base",
            ],
            catch_exceptions=False,
        )

        # Should fail due to missing required option
        assert result.exit_code == 2

    def test_keyword_analysis_with_job_desc(self, runner, temp_yaml_file, tmp_path):
        """Test keyword-analysis with job description."""
        job_desc = tmp_path / "job.txt"
        job_desc.write_text("Senior Python Engineer - FastAPI, PostgreSQL, Kubernetes")

        result = runner.invoke(
            cli,
            [
                "--yaml-path",
                str(temp_yaml_file),
                "keyword-analysis",
                "-v",
                "v1.0.0-base",
                "--job-desc",
                str(job_desc),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert "Keyword" in result.output or "Density" in result.output


class TestCLIJobParse:
    """Tests for job-parse command."""

    def test_job_parse_no_input(self, runner):
        """Test job-parse without input fails."""
        result = runner.invoke(
            cli,
            ["job-parse"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
        assert "--file" in result.output or "--url" in result.output

    def test_job_parse_with_file(self, runner, tmp_path):
        """Test job-parse with HTML file."""
        # Create a minimal HTML file
        html_file = tmp_path / "job.html"
        html_file.write_text("""
        <html>
        <body>
            <h1 class="job-details">Software Engineer at Test Corp</h1>
        </body>
        </html>
        """)

        result = runner.invoke(
            cli,
            [
                "job-parse",
                "--file",
                str(html_file),
            ],
            catch_exceptions=False,
        )

        # Should complete (parsing may not find data but shouldn't crash)
        assert "Error" not in result.output or result.exit_code == 0


class TestCLIHelp:
    """Tests for CLI help."""

    def test_main_help(self, runner):
        """Test main CLI help."""
        result = runner.invoke(cli, ["--help"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "Resume CLI" in result.output
        assert "generate" in result.output
        assert "validate" in result.output

    def test_command_help(self, runner):
        """Test generate command help."""
        result = runner.invoke(cli, ["generate", "--help"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "--variant" in result.output
        assert "--format" in result.output

    def test_version_option(self, runner):
        """Test CLI version option."""
        result = runner.invoke(cli, ["--version"], catch_exceptions=False)

        assert result.exit_code == 0
        # Should show version


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_yaml_path_at_top_level(self, runner):
        """Test CLI with invalid YAML path at top level."""
        result = runner.invoke(
            cli,
            ["--yaml-path", "/nonexistent/path.yaml", "validate"],
            catch_exceptions=False,
        )

        assert result.exit_code == 1
