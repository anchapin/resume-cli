"""Salary research and market data integration."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

# Initialize console
console = Console()


@dataclass
class SalaryData:
    """Salary data for a position."""

    title: str
    location: str
    company: str = ""
    min_salary: float = 0
    max_salary: float = 0
    median_salary: float = 0
    bonus_min: float = 0
    bonus_max: float = 0
    equity_min: float = 0
    equity_max: float = 0
    data_points: int = 0
    source: str = "Estimated"

    def total_compensation(self) -> tuple[float, float]:
        """Return (min, max) total compensation."""
        min_total = self.min_salary + self.bonus_min + self.equity_min
        max_total = self.max_salary + self.bonus_max + self.equity_max
        return min_total, max_total


class SalaryResearch:
    """Salary research tool for job positions."""

    # Sample salary ranges (in lieu of API access)
    # These are placeholder data that can be enhanced with real API integration
    BASE_SALARY_RANGES = {
        "software engineer": {
            "entry": (60000, 90000),
            "mid": (90000, 140000),
            "senior": (130000, 180000),
            "staff": (170000, 220000),
            "principal": (200000, 300000),
        },
        "backend engineer": {
            "entry": (65000, 95000),
            "mid": (95000, 145000),
            "senior": (135000, 185000),
            "staff": (175000, 230000),
            "principal": (210000, 320000),
        },
        "frontend engineer": {
            "entry": (60000, 90000),
            "mid": (90000, 140000),
            "senior": (130000, 175000),
            "staff": (165000, 215000),
            "principal": (195000, 290000),
        },
        "fullstack engineer": {
            "entry": (60000, 90000),
            "mid": (90000, 140000),
            "senior": (130000, 180000),
            "staff": (170000, 220000),
            "principal": (200000, 300000),
        },
        "data scientist": {
            "entry": (65000, 100000),
            "mid": (100000, 150000),
            "senior": (140000, 195000),
            "staff": (180000, 240000),
            "principal": (220000, 350000),
        },
        "machine learning engineer": {
            "entry": (75000, 110000),
            "mid": (110000, 160000),
            "senior": (150000, 210000),
            "staff": (190000, 260000),
            "principal": (240000, 400000),
        },
        "devops engineer": {
            "entry": (65000, 95000),
            "mid": (95000, 145000),
            "senior": (135000, 185000),
            "staff": (175000, 230000),
            "principal": (210000, 320000),
        },
        "product manager": {
            "entry": (70000, 100000),
            "mid": (100000, 150000),
            "senior": (140000, 195000),
            "staff": (180000, 240000),
            "principal": (220000, 350000),
        },
    }

    # Company multipliers (for top companies)
    COMPANY_MULTIPLIERS = {
        "google": 1.25,
        "meta": 1.25,
        "apple": 1.20,
        "amazon": 1.10,
        "netflix": 1.30,
        "stripe": 1.25,
        "airbnb": 1.20,
        "uber": 1.15,
        "lyft": 1.10,
        "salesforce": 1.15,
        "microsoft": 1.10,
        "adobe": 1.10,
    }

    # Location multipliers
    LOCATION_MULTIPLIERS = {
        "san francisco": 1.25,
        "new york": 1.20,
        "seattle": 1.15,
        "boston": 1.10,
        "los angeles": 1.10,
        "austin": 1.05,
        "denver": 1.05,
        "chicago": 1.05,
        "remote": 1.00,
    }

    def __init__(self):
        """Initialize salary research tool."""
        pass

    def research(
        self,
        title: str,
        location: str = "",
        company: str = "",
        experience_level: str = "mid",
    ) -> SalaryData:
        """
        Research salary for a position.

        Args:
            title: Job title
            location: Job location
            company: Company name
            experience_level: entry, mid, senior, staff, principal

        Returns:
            SalaryData object with salary information
        """
        # Normalize title
        title_lower = title.lower()

        # Find matching title range
        title_range = None
        for key, ranges in self.BASE_SALARY_RANGES.items():
            if key in title_lower:
                title_range = ranges
                break

        if title_range is None:
            # Default to software engineer range
            title_range = self.BASE_SALARY_RANGES["software engineer"]

        # Get base salary range
        if experience_level not in title_range:
            experience_level = "mid"

        min_salary, max_salary = title_range[experience_level]

        # Apply location multiplier
        location_mult = 1.0
        if location:
            location_lower = location.lower()
            for loc, mult in self.LOCATION_MULTIPLIERS.items():
                if loc in location_lower:
                    location_mult = mult
                    break

        min_salary *= location_mult
        max_salary *= location_mult

        # Apply company multiplier
        company_mult = 1.0
        if company:
            company_lower = company.lower()
            for comp, mult in self.COMPANY_MULTIPLIERS.items():
                if comp in company_lower:
                    company_mult = mult
                    break

        min_salary *= company_mult
        max_salary *= company_mult

        # Estimate bonus and equity (as percentage of base)
        bonus_pct = 0.15 if experience_level in ("senior", "staff", "principal") else 0.10
        bonus_min = min_salary * bonus_pct * 0.5
        bonus_max = min_salary * bonus_pct * 1.5

        equity_pct = 0.20 if experience_level in ("senior", "staff", "principal") else 0.10
        equity_min = min_salary * equity_pct * 0.5 if experience_level != "entry" else 0
        equity_max = min_salary * equity_pct * 2.0 if experience_level != "entry" else 0

        # Calculate median
        median_salary = (min_salary + max_salary) / 2

        return SalaryData(
            title=title,
            location=location,
            company=company,
            min_salary=round(min_salary, -3),
            max_salary=round(max_salary, -3),
            median_salary=round(median_salary, -3),
            bonus_min=round(bonus_min, -3),
            bonus_max=round(bonus_max, -3),
            equity_min=round(equity_min, -3),
            equity_max=round(equity_max, -3),
            data_points=100,  # Estimated
            source="Market Estimates",
        )

    def print_salary_report(self, salary_data: SalaryData) -> None:
        """Print salary report to console."""
        console.print("\n[bold blue]Salary Research Results[/bold blue]\n")

        # Title and location
        console.print(f"[cyan]Position:[/cyan] {salary_data.title}")
        if salary_data.location:
            console.print(f"[cyan]Location:[/cyan] {salary_data.location}")
        if salary_data.company:
            console.print(f"[cyan]Company:[/cyan] {salary_data.company}")
        console.print(
            f"[cyan]Source:[/cyan] {salary_data.source} ({salary_data.data_points} data points)"
        )
        console.print("")

        # Salary table
        table = Table(title="Compensation Breakdown")
        table.add_column("Component", style="cyan")
        table.add_column("Min", style="green", justify="right")
        table.add_column("Max", style="green", justify="right")

        table.add_row(
            "Base Salary", f"${salary_data.min_salary:,.0f}", f"${salary_data.max_salary:,.0f}"
        )
        table.add_row(
            "Annual Bonus", f"${salary_data.bonus_min:,.0f}", f"${salary_data.bonus_max:,.0f}"
        )

        if salary_data.equity_min > 0:
            table.add_row(
                "Equity/yr", f"${salary_data.equity_min:,.0f}", f"${salary_data.equity_max:,.0f}"
            )

        total_min, total_max = salary_data.total_compensation()
        table.add_row(
            "[bold]Total Comp[/bold]",
            f"[bold]${total_min:,.0f}[/bold]",
            f"[bold]${total_max:,.0f}[/bold]",
        )

        console.print(table)

        # Yearly breakdown
        console.print(f"\n[cyan]Median Base Salary:[/cyan] ${salary_data.median_salary:,.0f}")
        console.print(
            f"[cyan]Estimated Total:[/cyan] ${(total_min + total_max) / 2:,.0f} - ${(total_min + total_max) / 2 + 30000:,.0f}"
        )

        console.print("\n[yellow]Note:[/yellow] These are estimates based on market data.")
        console.print(
            "Actual salaries may vary based on specific skills, interviews, and negotiation."
        )

    def export_json(self, salary_data: SalaryData, output_path: Path) -> None:
        """Export salary data to JSON."""
        data = {
            "title": salary_data.title,
            "location": salary_data.location,
            "company": salary_data.company,
            "min_salary": salary_data.min_salary,
            "max_salary": salary_data.max_salary,
            "median_salary": salary_data.median_salary,
            "bonus_min": salary_data.bonus_min,
            "bonus_max": salary_data.bonus_max,
            "equity_min": salary_data.equity_min,
            "equity_max": salary_data.equity_max,
            "total_compensation_min": salary_data.total_compensation()[0],
            "total_compensation_max": salary_data.total_compensation()[1],
            "data_points": salary_data.data_points,
            "source": salary_data.source,
        }
        output_path.write_text(json.dumps(data, indent=2))


def research_salary(
    title: str,
    location: str = "",
    company: str = "",
    experience_level: str = "mid",
) -> SalaryData:
    """
    Research salary for a position.

    Args:
        title: Job title
        location: Job location
        company: Company name
        experience_level: entry, mid, senior, staff, principal

    Returns:
        SalaryData object
    """
    research = SalaryResearch()
    return research.research(title, location, company, experience_level)
