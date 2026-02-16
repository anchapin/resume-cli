#!/usr/bin/env python3
"""
Resume Performance Analyzer

Analyzes job application data to determine which resume versions perform best.
Tracks response rates, time-to-response, and application outcomes.

Usage:
    python analyze_performance.py
    python analyze_performance.py --csv tracking/resume_experiment.csv
    python analyze_performance.py --version v1.0.0-base
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


class ResumeAnalyzer:
    """Analyzes resume performance data from application tracking CSV."""

    def __init__(self, csv_path: str):
        """Initialize analyzer with CSV data."""
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Load CSV, skip comment lines
        self.df = pd.read_csv(self.csv_path, comment="#", parse_dates=["date_applied"])

        if len(self.df) == 0:
            print("⚠️  No application data found in CSV.")
            return

        # Data cleaning
        self.df["time_to_response_days"] = pd.to_numeric(
            self.df["time_to_response_days"], errors="coerce"
        ).fillna(0)

    def overview(self):
        """Print overall statistics."""
        print("\n" + "=" * 70)
        print("📊 RESUME PERFORMANCE ANALYSIS".center(70))
        print("=" * 70)

        total_apps = len(self.df)
        total_versions = self.df["resume_version"].nunique()
        date_range = f"{self.df['date_applied'].min().strftime('%Y-%m-%d')} to {self.df['date_applied'].max().strftime('%Y-%m-%d')}"

        print(f"\n📈 Overview:")
        print(f"   Total Applications: {total_apps}")
        print(f"   Resume Versions: {total_versions}")
        print(f"   Date Range: {date_range}")

        # Overall response stats
        responses = self.df[self.df["response_status"] != "no_response"]
        response_rate = len(responses) / total_apps * 100 if total_apps > 0 else 0

        print(f"\n📬 Overall Response Rate: {response_rate:.1f}% ({len(responses)}/{total_apps})")

    def analyze_by_version(self, version: Optional[str] = None):
        """Analyze performance metrics by resume version."""
        if version:
            df = self.df[self.df["resume_version"] == version]
            if len(df) == 0:
                print(f"\n⚠️  No data found for version: {version}")
                return
            print(f"\n🎯 Analysis for: {version}")
        else:
            df = self.df
            print("\n🎯 Performance by Resume Version:")

        if len(df) == 0:
            return

        print("\n" + "-" * 70)

        # Group by version
        for ver in df["resume_version"].unique():
            ver_df = df[df["resume_version"] == ver]
            total = len(ver_df)

            # Response breakdown
            status_counts = ver_df["response_status"].value_counts()
            interviews = status_counts.get("interview", 0)
            offers = status_counts.get("offer", 0)
            rejected = status_counts.get("rejected", 0)
            no_response = status_counts.get("no_response", 0)

            # Calculate rates
            response_rate = ((total - no_response) / total * 100) if total > 0 else 0
            interview_rate = (interviews / total * 100) if total > 0 else 0
            offer_rate = (offers / total * 100) if total > 0 else 0

            # Average time to response
            responded = ver_df[ver_df["time_to_response_days"] > 0]
            avg_time = responded["time_to_response_days"].mean() if len(responded) > 0 else 0

            print(f"\n   {ver}:")
            print(f"      Applications:    {total}")
            print(f"      Response Rate:   {response_rate:.1f}%")
            print(f"      Interview Rate:  {interview_rate:.1f}% ({interviews})")
            print(f"      Offer Rate:      {offer_rate:.1f}% ({offers})")
            print(f"      Rejected:        {rejected}")
            print(f"      No Response:     {no_response}")
            print(f"      Avg Response Time: {avg_time:.1f} days")

    def compare_versions(self):
        """Compare resume versions head-to-head."""
        versions = self.df["resume_version"].unique()
        if len(versions) < 2:
            print("\n⚠️  Need at least 2 resume versions to compare.")
            return

        print("\n🏆 Version Comparison:")
        print("-" * 70)

        # Create comparison DataFrame
        comparison = []
        for ver in versions:
            ver_df = self.df[self.df["resume_version"] == ver]
            total = len(ver_df)

            responses = ver_df[ver_df["response_status"] != "no_response"]
            interviews = ver_df[ver_df["response_status"] == "interview"]
            offers = ver_df[ver_df["response_status"] == "offer"]

            comparison.append(
                {
                    "Version": ver,
                    "Total": total,
                    "Response Rate": f"{(len(responses)/total*100):.1f}%" if total > 0 else "N/A",
                    "Interview Rate": f"{(len(interviews)/total*100):.1f}%" if total > 0 else "N/A",
                    "Offer Rate": f"{(len(offers)/total*100):.1f}%" if total > 0 else "N/A",
                    "Avg Response Days": (
                        f"{ver_df[ver_df['time_to_response_days']>0]['time_to_response_days'].mean():.1f}"
                        if len(ver_df[ver_df["time_to_response_days"] > 0]) > 0
                        else "N/A"
                    ),
                }
            )

        comp_df = pd.DataFrame(comparison)
        print(comp_df.to_string(index=False))

        # Find best performer
        if len(comparison) > 0:
            best_response = max(
                comparison,
                key=lambda x: (
                    float(x["Response Rate"].rstrip("%")) if x["Response Rate"] != "N/A" else 0
                ),
            )
            print(f"\n✨ Best Response Rate: {best_response['Version']}")

    def application_method_analysis(self):
        """Analyze performance by application method."""
        if "application_method" not in self.df.columns:
            return

        print("\n📮 Application Method Analysis:")
        print("-" * 70)

        for method in self.df["application_method"].dropna().unique():
            method_df = self.df[self.df["application_method"] == method]
            total = len(method_df)
            responses = method_df[method_df["response_status"] != "no_response"]
            response_rate = (len(responses) / total * 100) if total > 0 else 0

            print(f"   {method}: {response_rate:.1f}% ({len(responses)}/{total})")

    def recent_applications(self, n: int = 5):
        """Show most recent applications."""
        print(f"\n📅 Most Recent {n} Applications:")
        print("-" * 70)

        recent = self.df.nlargest(n, "date_applied")
        for _, row in recent.iterrows():
            status_icon = {
                "no_response": "⏳",
                "rejected": "❌",
                "interview": "📞",
                "offer": "🎉",
                "withdrawn": "🔙",
            }.get(row["response_status"], "❓")

            print(
                f"   {status_icon} {row['date_applied'].strftime('%Y-%m-%d')} | {row['company'][:20]:20} | {row['role'][:25]:25} | {row['resume_version']}"
            )

    def recommendations(self):
        """Provide data-driven recommendations."""
        print("\n💡 Recommendations:")
        print("-" * 70)

        versions = self.df["resume_version"].unique()

        # Find underperforming versions
        underperformers = []
        for ver in versions:
            ver_df = self.df[self.df["resume_version"] == ver]
            if len(ver_df) >= 5:  # Only if enough data
                response_rate = (
                    len(ver_df[ver_df["response_status"] != "no_response"]) / len(ver_df)
                ) * 100
                if response_rate < 20:  # Below 20% response rate
                    underperformers.append((ver, response_rate))

        if underperformers:
            print("\n   ⚠️  Consider retiring these versions (low response rate):")
            for ver, rate in underperformers:
                print(f"      • {ver}: {rate:.1f}% response rate")
        else:
            print(
                "\n   ✅ All versions are performing adequately (need more data to identify underperformers)"
            )

        # Find top performer
        if len(versions) > 0:
            best_ver = None
            best_rate = 0
            for ver in versions:
                ver_df = self.df[self.df["resume_version"] == ver]
                if len(ver_df) >= 3:
                    response_rate = (
                        len(ver_df[ver_df["response_status"] != "no_response"]) / len(ver_df)
                    ) * 100
                    if response_rate > best_rate:
                        best_rate = response_rate
                        best_ver = ver

            if best_ver:
                print(f"\n   🏆 Top performer: {best_ver} ({best_rate:.1f}% response rate)")
                print(
                    f"      Consider using this version more frequently or using it as template for variants."
                )

    def generate_report(self, version: Optional[str] = None):
        """Generate complete performance report."""
        self.overview()
        self.analyze_by_version(version)
        if not version:
            self.compare_versions()
        self.application_method_analysis()
        self.recent_applications()
        self.recommendations()
        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze resume performance from application tracking data"
    )
    parser.add_argument(
        "--csv",
        default="tracking/resume_experiment.csv",
        help="Path to CSV file (default: tracking/resume_experiment.csv)",
    )
    parser.add_argument("--version", help="Analyze specific resume version only")

    args = parser.parse_args()

    try:
        analyzer = ResumeAnalyzer(args.csv)
        analyzer.generate_report(version=args.version)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you've created the tracking CSV file.")
        print("   Copy tracking/template.csv to tracking/resume_experiment.csv")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
