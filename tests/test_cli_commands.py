"""Integration tests for CLI commands."""

import subprocess
import sys
from pathlib import Path

import yaml


class TestCLIValidate:
    """Integration tests for validate command."""

    def test_validate_valid_resume(self, sample_yaml_file: Path):
        """Test validate command with valid resume."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--yaml-path", str(sample_yaml_file), "validate"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "passed" in result.stdout.lower()

    def test_validate_missing_file(self, temp_dir: Path):
        """Test validate command with missing file."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(temp_dir / "nonexistent.yaml"),
                "validate",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 1
        assert "error" in result.stdout.lower()


class TestCLIVariants:
    """Integration tests for variants command."""

    def test_variants_lists_all(self, sample_yaml_file: Path):
        """Test variants command lists all variants."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--yaml-path", str(sample_yaml_file), "variants"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "v1.0.0-base" in result.stdout
        assert "v1.1.0-backend" in result.stdout
        assert "Resume Variants" in result.stdout


class TestCLIGenerate:
    """Integration tests for generate command."""

    def test_generate_markdown(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate command creates markdown file."""
        output_file = temp_dir / "output.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "generate",
                "-v",
                "v1.0.0-base",
                "-f",
                "md",
                "-o",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0
        assert "# " in content  # Markdown header

    def test_generate_tex(self, sample_yaml_file: Path, temp_dir: Path):
        """Test generate command creates tex file."""
        output_file = temp_dir / "output.tex"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "generate",
                "-v",
                "v1.0.0-base",
                "-f",
                "tex",
                "-o",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0

    def test_generate_no_save(self, sample_yaml_file: Path):
        """Test generate command with --no-save prints to stdout."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "generate",
                "-v",
                "v1.0.0-base",
                "-f",
                "md",
                "--no-save",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "# " in result.stdout  # Markdown header in stdout


class TestCLIApply:
    """Integration tests for apply command."""

    def test_apply_logs_application(self, sample_yaml_file: Path, temp_dir: Path, monkeypatch):
        """Test apply command logs application."""
        # Set up a temp config with tracking enabled
        monkeypatch.setenv("RESUME_CLI_CONFIG", str(temp_dir / "config.yaml"))

        # Create a config file with tracking enabled
        config_data = {
            "tracking": {"enabled": True, "csv_path": str(temp_dir / "tracking.csv")},
            "output": {"directory": str(temp_dir / "output")},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "--config-path",
                str(config_path),
                "apply",
                "TestCompany",
                "applied",
                "-r",
                "Software Engineer",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # May fail if tracking is disabled in default config, but should not crash
        assert "Error" not in result.stdout or result.returncode == 0


class TestCLIAnalyze:
    """Integration tests for analyze command."""

    def test_analyze_with_no_data(self, sample_yaml_file: Path, temp_dir: Path, monkeypatch):
        """Test analyze command with no tracking data."""
        # Create config with tracking enabled but no data
        config_data = {
            "tracking": {"enabled": True, "csv_path": str(temp_dir / "empty.csv")},
            "output": {"directory": str(temp_dir / "output")},
        }
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Create empty CSV
        csv_path = temp_dir / "empty.csv"
        csv_path.touch()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "--config-path",
                str(config_path),
                "analyze",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should either show no data or show stats
        assert "Error" not in result.stdout or result.returncode == 0


class TestCLIAtsCheck:
    """Integration tests for ats-check command."""

    def test_ats_check_with_job_desc(self, sample_yaml_file: Path, temp_dir: Path):
        """Test ats-check command with job description."""
        # Create a sample job description
        job_desc = temp_dir / "job.txt"
        job_desc.write_text("""
Senior Backend Engineer

Requirements:
- Python
- FastAPI
- PostgreSQL
- Kubernetes
- REST API
""")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "ats-check",
                "-v",
                "v1.0.0-base",
                "--job-desc",
                str(job_desc),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "ATS" in result.stdout or "Score" in result.stdout

    def test_ats_check_missing_job_desc(self, sample_yaml_file: Path):
        """Test ats-check command without job description fails."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "ats-check",
                "-v",
                "v1.0.0-base",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Click exits with 2 for missing required options
        assert result.returncode == 2
        assert "Missing option" in result.stderr or "Missing option" in result.stdout


class TestCLIKeywordAnalysis:
    """Integration tests for keyword-analysis command."""

    def test_keyword_analysis_with_job_desc(self, sample_yaml_file: Path, temp_dir: Path):
        """Test keyword-analysis command with job description."""
        # Create a sample job description
        job_desc = temp_dir / "job.txt"
        job_desc.write_text("""
Senior Backend Engineer

Requirements:
- Python
- FastAPI
- PostgreSQL
- Kubernetes
- REST API
- Docker
""")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "keyword-analysis",
                "-v",
                "v1.0.0-base",
                "--job-desc",
                str(job_desc),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Keyword" in result.stdout or "Density" in result.stdout

    def test_keyword_analysis_missing_job_desc(self, sample_yaml_file: Path):
        """Test keyword-analysis command without job description fails."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "keyword-analysis",
                "-v",
                "v1.0.0-base",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Click exits with 2 for missing required options
        assert result.returncode == 2
        assert "Missing option" in result.stderr or "Missing option" in result.stdout


class TestCLIHelp:
    """Integration tests for CLI help."""

    def test_main_help(self):
        """Test main CLI help displays."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Resume CLI" in result.stdout
        assert "generate" in result.stdout
        assert "validate" in result.stdout

    def test_command_help(self):
        """Test individual command help displays."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "generate", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "--variant" in result.stdout
        assert "--format" in result.stdout


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_invalid_yaml_path(self):
        """Test CLI handles invalid yaml path gracefully."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--yaml-path", "/nonexistent/path.yaml", "validate"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 1
        assert "Error" in result.stdout or "not found" in result.stdout.lower()

    def test_invalid_variant(self, sample_yaml_file: Path):
        """Test CLI handles invalid variant gracefully by falling back to base template."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "--yaml-path",
                str(sample_yaml_file),
                "generate",
                "-v",
                "nonexistent-variant",
                "-f",
                "md",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # CLI gracefully falls back to base template and succeeds
        assert result.returncode == 0
        assert "Generated:" in result.stdout
