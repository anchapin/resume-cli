"""Integration with CSV-based application tracking."""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import csv


class TrackingIntegration:
    """Handle application tracking CSV integration."""

    def __init__(self, config):
        """
        Initialize tracking integration.

        Args:
            config: Config object with tracking settings
        """
        self.config = config
        self.csv_path = config.tracking_csv_path

    def log_application(
        self,
        company: str,
        role: str,
        status: str,
        variant: str = "v1.0.0-base",
        source: str = "manual",
        url: Optional[str] = None,
        notes: Optional[str] = None,
        cover_letter_generated: bool = False,
        package_path: Optional[str] = None
    ) -> None:
        """
        Log a job application to CSV.

        Args:
            company: Company name
            role: Job title/role
            status: Application status
            variant: Resume variant used
            source: Application source
            url: Job posting URL
            notes: Additional notes
            cover_letter_generated: Whether a cover letter was generated
            package_path: Path to the application package directory
        """
        # Ensure CSV exists
        self._ensure_csv_exists()

        # Read existing entries
        entries = self._read_csv()

        # Add new entry
        entry = {
            "resume_version": variant,
            "company": company,
            "role": role,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": status,
            "response": "0",  # Will update if response received
            "notes": notes or "",
            "source": source,
            "url": url or "",
            "cover_letter": "1" if cover_letter_generated else "0",
            "package_path": package_path or ""
        }

        entries.append(entry)

        # Write back
        self._write_csv(entries)

    def _ensure_csv_exists(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
                writer.writeheader()

    def _get_fieldnames(self) -> list:
        """Get CSV field names."""
        return [
            "resume_version",
            "company",
            "role",
            "date",
            "status",
            "response",
            "notes",
            "source",
            "url",
            "cover_letter",
            "package_path"
        ]

    def _read_csv(self) -> list:
        """Read all entries from CSV."""
        entries = []

        if not self.csv_path.exists():
            return entries

        with open(self.csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)

        return entries

    def _write_csv(self, entries: list) -> None:
        """Write entries to CSV."""
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
            writer.writeheader()
            writer.writerows(entries)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate application statistics.

        Returns:
            Dictionary with statistics
        """
        entries = self._read_csv()

        total = len(entries)
        if total == 0:
            return {
                "total": 0,
                "applied": 0,
                "interview": 0,
                "offer": 0,
                "response_rate": 0.0
            }

        # Count by status
        status_counts = {}
        for entry in entries:
            status = entry.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate response rate
        responses = sum(1 for e in entries if e.get("response") == "1")
        response_rate = (responses / total * 100) if total > 0 else 0

        return {
            "total": total,
            "applied": status_counts.get("applied", 0),
            "interview": status_counts.get("interview", 0),
            "offer": status_counts.get("offer", 0),
            "response_rate": response_rate,
            "by_status": status_counts
        }

    def get_recent_applications(self, limit: int = 10) -> list:
        """
        Get recent applications.

        Args:
            limit: Maximum number to return

        Returns:
            List of application entries
        """
        entries = self._read_csv()
        # Sort by date descending
        entries.sort(key=lambda e: e.get("date", ""), reverse=True)
        return entries[:limit]

    def update_status(
        self,
        company: str,
        new_status: str,
        role: Optional[str] = None
    ) -> bool:
        """
        Update application status.

        Args:
            company: Company name
            new_status: New status value
            role: Optional role to disambiguate

        Returns:
            True if updated, False if not found
        """
        entries = self._read_csv()
        updated = False

        for entry in entries:
            if entry["company"].lower() == company.lower():
                if role is None or entry.get("role", "").lower() == role.lower():
                    entry["status"] = new_status

                    # Mark as response if moving from applied
                    if new_status in ["interview", "offer", "rejected"]:
                        entry["response"] = "1"

                    updated = True
                    break

        if updated:
            self._write_csv(entries)

        return updated
