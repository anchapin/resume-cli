"""Integration with CSV-based application tracking."""

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional



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
        package_path: Optional[str] = None,
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
            "package_path": package_path or "",
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
            "package_path",
        ]

    def _read_csv(self) -> list:
        """Read all entries from CSV."""
        entries = []

        if not self.csv_path.exists():
            return entries

        with open(self.csv_path, newline="") as f:
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
            return {"total": 0, "applied": 0, "interview": 0, "offer": 0, "response_rate": 0.0}

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
            "by_status": status_counts,
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

    def update_status(self, company: str, new_status: str, role: Optional[str] = None) -> bool:
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

    # =========================================================================
    # Analytics Methods for Dashboard
    # =========================================================================

    def get_applications_by_status(self) -> Dict[str, int]:
        """
        Get application counts grouped by status.

        Returns:
            Dictionary mapping status to count
        """
        entries = self._read_csv()
        status_counts = defaultdict(int)

        for entry in entries:
            status = entry.get("status", "unknown")
            status_counts[status] += 1

        return dict(status_counts)

    def get_applications_timeline(self, days: int = 90) -> List[Dict[str, Any]]:
        """
        Get application counts over time (daily).

        Args:
            days: Number of days to look back

        Returns:
            List of dicts with 'date' and 'count' keys
        """
        entries = self._read_csv()
        cutoff_date = datetime.now() - timedelta(days=days)

        # Count applications per date
        date_counts = defaultdict(int)
        for entry in entries:
            try:
                entry_date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
                if entry_date >= cutoff_date:
                    date_counts[entry.get("date", "")] += 1
            except (ValueError, TypeError):
                continue

        # Generate timeline with all dates in range
        timeline = []
        current_date = cutoff_date
        while current_date <= datetime.now():
            date_str = current_date.strftime("%Y-%m-%d")
            timeline.append({"date": date_str, "count": date_counts.get(date_str, 0)})
            current_date += timedelta(days=1)

        return timeline

    def get_variant_performance(self) -> List[Dict[str, Any]]:
        """
        Get performance metrics by resume variant.

        Returns:
            List of dicts with variant performance data
        """
        entries = self._read_csv()

        # Group by variant
        variant_data = defaultdict(
            lambda: {
                "total": 0,
                "applied": 0,
                "interview": 0,
                "offer": 0,
                "rejected": 0,
                "responses": 0,
            }
        )

        for entry in entries:
            variant = entry.get("resume_version", "unknown")
            status = entry.get("status", "unknown")
            response = entry.get("response", "0")

            variant_data[variant]["total"] += 1

            if status == "applied":
                variant_data[variant]["applied"] += 1
            elif status == "interview":
                variant_data[variant]["interview"] += 1
            elif status == "offer":
                variant_data[variant]["offer"] += 1
            elif status == "rejected":
                variant_data[variant]["rejected"] += 1

            if response == "1":
                variant_data[variant]["responses"] += 1

        # Calculate rates
        result = []
        for variant, data in variant_data.items():
            total = data["total"]
            result.append(
                {
                    "variant": variant,
                    "total_applications": total,
                    "response_rate": (data["responses"] / total * 100) if total > 0 else 0,
                    "interview_rate": (data["interview"] / total * 100) if total > 0 else 0,
                    "offer_rate": (data["offer"] / total * 100) if total > 0 else 0,
                    "rejection_rate": (data["rejected"] / total * 100) if total > 0 else 0,
                    "interviews": data["interview"],
                    "offers": data["offer"],
                    "rejected": data["rejected"],
                }
            )

        # Sort by total applications descending
        result.sort(key=lambda x: x["total_applications"], reverse=True)
        return result

    def get_company_analytics(self) -> List[Dict[str, Any]]:
        """
        Get analytics grouped by company.

        Returns:
            List of dicts with company data
        """
        entries = self._read_csv()

        # Group by company
        company_data = defaultdict(lambda: {"applications": [], "statuses": defaultdict(int)})

        for entry in entries:
            company = entry.get("company", "Unknown")
            status = entry.get("status", "unknown")
            company_data[company]["applications"].append(entry)
            company_data[company]["statuses"][status] += 1

        result = []
        for company, data in company_data.items():
            apps = data["applications"]
            statuses = data["statuses"]

            # Get unique roles
            roles = list(set(app.get("role", "") for app in apps))

            # Get latest application date
            dates = [app.get("date", "") for app in apps if app.get("date")]
            latest_date = max(dates) if dates else ""

            # Get sources
            sources = list(set(app.get("source", "") for app in apps))

            result.append(
                {
                    "company": company,
                    "total_applications": len(apps),
                    "roles": roles,
                    "latest_application": latest_date,
                    "statuses": dict(statuses),
                    "sources": sources,
                    "has_response": any(app.get("response") == "1" for app in apps),
                }
            )

        # Sort by total applications descending
        result.sort(key=lambda x: x["total_applications"], reverse=True)
        return result

    def get_response_rate_gauge(self) -> Dict[str, Any]:
        """
        Get overall response rate for gauge display.

        Returns:
            Dict with response_rate, interviews, offers, total
        """
        stats = self.get_statistics()
        return {
            "response_rate": stats.get("response_rate", 0),
            "interview_rate": (
                (stats.get("interview", 0) / stats.get("total", 1) * 100)
                if stats.get("total", 0) > 0
                else 0
            ),
            "offer_rate": (
                (stats.get("offer", 0) / stats.get("total", 1) * 100)
                if stats.get("total", 0) > 0
                else 0
            ),
            "total_applications": stats.get("total", 0),
            "interviews": stats.get("interview", 0),
            "offers": stats.get("offer", 0),
        }

    def get_source_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get application counts by source.

        Returns:
            List of dicts with source and count
        """
        entries = self._read_csv()
        source_counts = defaultdict(int)

        for entry in entries:
            source = entry.get("source", "unknown")
            source_counts[source] += 1

        result = [{"source": source, "count": count} for source, count in source_counts.items()]
        result.sort(key=lambda x: x["count"], reverse=True)
        return result

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for analytics.

        Returns:
            Dictionary with dashboard data including:
            - overview: response_rate, interview_rate, offer_rate, total_applications, interviews, offers
            - by_status: breakdown by application status
            - timeline: applications over time
            - variant_performance: performance by resume variant
            - company_analytics: analytics grouped by company
            - source_breakdown: breakdown by application source
        """
        return {
            "overview": self.get_response_rate_gauge(),
            "by_status": self.get_applications_by_status(),
            "timeline": self.get_applications_timeline(days=90),
            "variant_performance": self.get_variant_performance(),
            "company_analytics": self.get_company_analytics(),
            "source_breakdown": self.get_source_breakdown(),
        }
