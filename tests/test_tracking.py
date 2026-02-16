"""Unit tests for TrackingIntegration class."""

import csv
import os
from datetime import datetime
from pathlib import Path

import pytest

from cli.integrations.tracking import TrackingIntegration
from cli.utils.config import Config


class TestTrackingIntegrationInitialization:
    """Test TrackingIntegration initialization."""

    def test_init_with_config(self, mock_config: Config):
        """Test initialization with config."""
        tracking = TrackingIntegration(mock_config)

        assert tracking.config == mock_config
        assert tracking.csv_path == mock_config.tracking_csv_path


class TestEnsureCSVExists:
    """Test _ensure_csv_exists method."""

    def test_ensure_csv_creates_file(self, mock_config: Config, temp_dir: Path):
        """Test _ensure_csv creates CSV with headers if not exists."""
        csv_path = temp_dir / "test_tracking.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking._ensure_csv_exists()

        assert csv_path.exists()

        # Check headers
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert "resume_version" in headers
        assert "company" in headers
        assert "role" in headers
        assert "date" in headers
        assert "status" in headers

    def test_ensure_csv_creates_directories(self, mock_config: Config, temp_dir: Path):
        """Test _ensure_csv creates parent directories."""
        csv_path = temp_dir / "nested" / "dir" / "tracking.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking._ensure_csv_exists()

        assert csv_path.parent.exists()
        assert csv_path.exists()

    def test_ensure_csv_skips_if_exists(self, mock_config: Config, sample_csv_file: Path):
        """Test _ensure_csv doesn't recreate existing file."""
        csv_path = sample_csv_file
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Create file first
        tracking._ensure_csv_exists()

        # Record modification time
        mtime_before = csv_path.stat().st_mtime

        # Call again
        tracking._ensure_csv_exists()

        # File should not be recreated
        mtime_after = csv_path.stat().st_mtime
        assert mtime_before == mtime_after


class TestLogApplication:
    """Test log_application method."""

    def test_log_application_adds_entry(self, mock_config: Config, temp_dir: Path):
        """Test log_application adds entry to CSV."""
        csv_path = temp_dir / "test_tracking.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(
            company="Acme Corp", role="Senior Engineer", status="applied", variant="v1.0.0-base"
        )

        # Read CSV
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        assert len(entries) == 1
        assert entries[0]["company"] == "Acme Corp"
        assert entries[0]["role"] == "Senior Engineer"
        assert entries[0]["status"] == "applied"
        assert entries[0]["resume_version"] == "v1.0.0-base"

    def test_log_application_with_optional_fields(self, mock_config: Config, temp_dir: Path):
        """Test log_application with all optional fields."""
        csv_path = temp_dir / "test_tracking.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(
            company="Startup Inc",
            role="Engineer",
            status="applied",
            variant="v1.1.0-backend",
            source="LinkedIn",
            url="https://example.com/job",
            notes="Referred by John",
            cover_letter_generated=True,
            package_path="/output/acme-2024-01-15",
        )

        # Read CSV
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entry = list(reader)[0]

        assert entry["source"] == "LinkedIn"
        assert entry["url"] == "https://example.com/job"
        assert entry["notes"] == "Referred by John"
        assert entry["cover_letter"] == "1"
        assert entry["package_path"] == "/output/acme-2024-01-15"

    def test_log_appends_to_existing_entries(self, mock_config: Config, temp_dir: Path):
        """Test log_application appends to existing data."""
        csv_path = temp_dir / "test_tracking.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Log first application
        tracking.log_application(company="Company A", role="Role A", status="applied")

        # Log second application
        tracking.log_application(company="Company B", role="Role B", status="applied")

        # Read CSV
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        assert len(entries) == 2
        assert entries[0]["company"] == "Company A"
        assert entries[1]["company"] == "Company B"


class TestGetStatistics:
    """Test get_statistics method."""

    def test_get_statistics_empty_csv(self, mock_config: Config, temp_dir: Path):
        """Test get_statistics with empty CSV."""
        csv_path = temp_dir / "empty.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        stats = tracking.get_statistics()

        assert stats["total"] == 0
        assert stats["applied"] == 0
        assert stats["interview"] == 0
        assert stats["offer"] == 0
        assert stats["response_rate"] == 0.0

    def test_get_statistics_with_data(self, mock_config: Config, temp_dir: Path):
        """Test get_statistics calculates correct statistics."""
        csv_path = temp_dir / "stats.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Add various applications
        tracking.log_application(company="A", role="R1", status="applied")
        tracking.log_application(company="B", role="R2", status="interview")
        tracking.log_application(company="C", role="R3", status="offer")
        tracking.log_application(company="D", role="R4", status="rejected")

        # Manually set response for some
        entries = tracking._read_csv()
        entries[0]["response"] = "1"  # Got response
        entries[2]["response"] = "1"  # Got response
        tracking._write_csv(entries)

        stats = tracking.get_statistics()

        assert stats["total"] == 4
        assert stats["applied"] == 1
        assert stats["interview"] == 1
        assert stats["offer"] == 1
        assert stats["response_rate"] == 50.0  # 2 out of 4

    def test_get_statistics_includes_by_status(self, mock_config: Config, temp_dir: Path):
        """Test get_statistics includes breakdown by status."""
        csv_path = temp_dir / "by_status.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(company="A", role="R1", status="applied")
        tracking.log_application(company="B", role="R2", status="applied")
        tracking.log_application(company="C", role="R3", status="interview")

        stats = tracking.get_statistics()

        assert "by_status" in stats
        assert stats["by_status"]["applied"] == 2
        assert stats["by_status"]["interview"] == 1


class TestGetRecentApplications:
    """Test get_recent_applications method."""

    def test_get_recent_applications_limit(self, mock_config: Config, temp_dir: Path):
        """Test get_recent_applications respects limit."""
        csv_path = temp_dir / "recent.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Add 15 applications
        for i in range(15):
            tracking.log_application(company=f"Company {i}", role=f"Role {i}", status="applied")

        # Get recent
        recent = tracking.get_recent_applications(limit=5)

        assert len(recent) == 5

        # Should be sorted by date descending (all have same date in test)
        # Stable sort preserves original order for ties
        assert recent[0]["company"] == "Company 0"
        assert recent[4]["company"] == "Company 4"

    def test_get_recent_applications_default_limit(self, mock_config: Config, temp_dir: Path):
        """Test get_recent_applications uses default limit."""
        csv_path = temp_dir / "recent_default.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Add 5 applications
        for i in range(5):
            tracking.log_application(company=f"Company {i}", role=f"Role {i}", status="applied")

        # Get recent without limit (uses default 10)
        recent = tracking.get_recent_applications()

        assert len(recent) == 5  # Only 5 added


class TestUpdateStatus:
    """Test update_status method."""

    def test_update_status_success(self, mock_config: Config, temp_dir: Path):
        """Test update_status updates application status."""
        csv_path = temp_dir / "update.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(company="Acme", role="Engineer", status="applied")

        # Update status
        updated = tracking.update_status(company="Acme", new_status="interview")

        assert updated is True

        # Verify
        entries = tracking._read_csv()
        assert entries[0]["status"] == "interview"

    def test_update_status_marks_response(self, mock_config: Config, temp_dir: Path):
        """Test update_status marks response when moving from applied."""
        csv_path = temp_dir / "response.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(company="Acme", role="Engineer", status="applied")

        # Update to interview
        tracking.update_status(company="Acme", new_status="interview")

        entries = tracking._read_csv()
        assert entries[0]["response"] == "1"

    def test_update_status_disambiguate_by_role(self, mock_config: Config, temp_dir: Path):
        """Test update_status uses role to disambiguate."""
        csv_path = temp_dir / "disambiguate.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Add two applications for same company
        tracking.log_application(company="Acme", role="Engineer", status="applied")
        tracking.log_application(company="Acme", role="Manager", status="applied")

        # Update Manager role
        updated = tracking.update_status(company="Acme", new_status="interview", role="Manager")

        assert updated is True

        # Verify only Manager was updated
        entries = tracking._read_csv()
        assert entries[1]["status"] == "interview"
        assert entries[0]["status"] == "applied"  # Engineer unchanged

    def test_update_status_not_found(self, mock_config: Config, temp_dir: Path):
        """Test update_status returns False when company not found."""
        csv_path = temp_dir / "not_found.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(company="Acme", role="Engineer", status="applied")

        # Try to update non-existent company
        updated = tracking.update_status(company="NonExistent", new_status="interview")

        assert updated is False

    def test_update_status_case_insensitive(self, mock_config: Config, temp_dir: Path):
        """Test update_status matches company case-insensitively."""
        csv_path = temp_dir / "case.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking.log_application(company="Acme Corp", role="Engineer", status="applied")

        # Update with different case
        updated = tracking.update_status(company="acme corp", new_status="interview")

        assert updated is True
        entries = tracking._read_csv()
        assert entries[0]["status"] == "interview"


class TestReadWriteCSV:
    """Test _read_csv and _write_csv methods."""

    def test_read_csv_empty(self, mock_config: Config, temp_dir: Path):
        """Test _read_csv returns empty list for non-existent file."""
        csv_path = temp_dir / "nonexistent.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        entries = tracking._read_csv()

        assert entries == []

    def test_read_csv_existing(self, mock_config: Config, sample_csv_file: Path):
        """Test _read_csv reads existing CSV."""
        config = Config()
        config.set("tracking.csv_path", str(sample_csv_file))

        tracking = TrackingIntegration(config)
        entries = tracking._read_csv()

        # Just verify it works
        assert isinstance(entries, list)

    def test_write_csv_creates_headers(self, mock_config: Config, temp_dir: Path):
        """Test _write_csv writes headers."""
        csv_path = temp_dir / "write.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)
        tracking._write_csv([{"company": "Test"}])

        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert "resume_version" in headers
        assert "company" in headers

    def test_write_csv_overwrites(self, mock_config: Config, temp_dir: Path):
        """Test _write_csv overwrites existing file."""
        csv_path = temp_dir / "overwrite.csv"
        config = Config()
        config.set("tracking.csv_path", str(csv_path))

        tracking = TrackingIntegration(config)

        # Write first version
        tracking._write_csv([{"company": "A", "role": "R1"}])

        # Write second version (overwrites)
        tracking._write_csv([{"company": "B", "role": "R2"}])

        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            entries = list(reader)

        assert len(entries) == 1
        assert entries[0]["company"] == "B"


class TestGetFieldnames:
    """Test _get_fieldnames method."""

    def test_get_fieldnames(self, mock_config: Config):
        """Test _get_fieldnames returns correct field names."""
        config = mock_config
        tracking = TrackingIntegration(config)

        fieldnames = tracking._get_fieldnames()

        assert "resume_version" in fieldnames
        assert "company" in fieldnames
        assert "role" in fieldnames
        assert "date" in fieldnames
        assert "status" in fieldnames
        assert "response" in fieldnames
        assert "notes" in fieldnames
        assert "source" in fieldnames
        assert "url" in fieldnames
        assert "cover_letter" in fieldnames
        assert "package_path" in fieldnames
        assert len(fieldnames) == 11
