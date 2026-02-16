"""Offer comparison and decision tool for job offers."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

# Initialize console
console = Console()


@dataclass
class Offer:
    """Represents a job offer."""

    company: str
    role: str
    base_salary: float = 0
    bonus: float = 0
    equity: float = 0
    equity_years: int = 4
    benefits_value: float = 0
    location: str = ""
    remote: bool = False
    notes: str = ""

    def __post_init__(self):
        """Calculate total compensation."""
        self.total_compensation = self.base_salary + self.bonus + (self.equity / self.equity_years)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Offer":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class UserPriorities:
    """User's priorities for offer comparison."""

    salary_weight: int = 30
    growth_weight: int = 25
    wlb_weight: int = 25  # Work-life balance
    benefits_weight: int = 20

    def total(self) -> int:
        """Return total weight."""
        return self.salary_weight + self.growth_weight + self.wlb_weight + self.benefits_weight

    def normalize(self) -> Dict[str, float]:
        """Return normalized weights (0-1)."""
        total = self.total()
        if total == 0:
            return {"salary": 0.25, "growth": 0.25, "wlb": 0.25, "benefits": 0.25}
        return {
            "salary": self.salary_weight / total,
            "growth": self.growth_weight / total,
            "wlb": self.wlb_weight / total,
            "benefits": self.benefits_weight / total,
        }


@dataclass
class OfferScores:
    """Scored offer with weighted scores."""

    offer: Offer
    compensation_score: float = 0
    growth_score: float = 0
    wlb_score: float = 0  # Work-life balance
    benefits_score: float = 0
    weighted_score: float = 0


class OfferComparison:
    """Compare and analyze job offers."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize offer comparison.

        Args:
            storage_path: Path to store offers JSON file
        """
        if storage_path is None:
            storage_path = Path.home() / ".resume-cli" / "offers.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.offers: List[Offer] = []
        self.priorities = UserPriorities()
        self._load_offers()

    def _load_offers(self) -> None:
        """Load offers from storage file."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.offers = [Offer.from_dict(o) for o in data.get("offers", [])]
                if "priorities" in data:
                    self.priorities = UserPriorities(**data["priorities"])
            except (json.JSONDecodeError, KeyError):
                self.offers = []

    def _save_offers(self) -> None:
        """Save offers to storage file."""
        data = {
            "offers": [o.to_dict() for o in self.offers],
            "priorities": {
                "salary_weight": self.priorities.salary_weight,
                "growth_weight": self.priorities.growth_weight,
                "wlb_weight": self.priorities.wlb_weight,
                "benefits_weight": self.priorities.benefits_weight,
            },
        }
        self.storage_path.write_text(json.dumps(data, indent=2))

    def add_offer(self, offer: Offer) -> None:
        """Add a new offer."""
        self.offers.append(offer)
        self._save_offers()

    def remove_offer(self, company: str) -> bool:
        """Remove an offer by company name."""
        initial_len = len(self.offers)
        self.offers = [o for o in self.offers if o.company.lower() != company.lower()]
        if len(self.offers) < initial_len:
            self._save_offers()
            return True
        return False

    def update_priorities(self, priorities: UserPriorities) -> None:
        """Update user priorities."""
        self.priorities = priorities
        self._save_offers()

    def compare_offers(self) -> List[OfferScores]:
        """
        Compare all offers and return scored results.

        Returns:
            List of OfferScores sorted by weighted score (highest first)
        """
        if not self.offers:
            return []

        # Find max values for normalization
        max_salary = max(o.total_compensation for o in self.offers) or 1
        max_benefits = max(o.benefits_value for o in self.offers) or 1

        # Get normalized weights
        weights = self.priorities.normalize()

        scored_offers = []
        for offer in self.offers:
            scores = OfferScores(offer=offer)

            # Compensation score (0-10)
            scores.compensation_score = (offer.total_compensation / max_salary) * 10

            # Benefits score (0-10)
            scores.benefits_score = (
                (offer.benefits_value / max_benefits) * 10 if max_benefits > 0 else 5
            )

            # Growth score (default based on equity)
            scores.growth_score = min(10, (offer.equity / 100000) * 10) if offer.equity > 0 else 5

            # Work-life balance score (default based on remote)
            scores.wlb_score = 8 if offer.remote else 5

            # Calculate weighted score
            scores.weighted_score = (
                scores.compensation_score * weights["salary"]
                + scores.growth_score * weights["growth"]
                + scores.wlb_score * weights["wlb"]
                + scores.benefits_score * weights["benefits"]
            )

            scored_offers.append(scores)

        # Sort by weighted score
        scored_offers.sort(key=lambda x: x.weighted_score, reverse=True)
        return scored_offers

    def generate_comparison_report(self) -> str:
        """Generate a comparison report in Markdown format."""
        if not self.offers:
            return "# No Offers to Compare\n\nAdd offers using `resume-cli offer-add` command."

        lines = []
        lines.append("# Offer Comparison Report")
        lines.append("")

        # Get scored offers
        scored_offers = self.compare_offers()

        # Compensation table
        lines.append("## Compensation Comparison")
        lines.append("")

        table = Table()
        table.add_column("Company", style="cyan")
        table.add_column("Base Salary", style="green", justify="right")
        table.add_column("Bonus", style="green", justify="right")
        table.add_column("Equity (yr)", style="green", justify="right")
        table.add_column("Total/yr", style="yellow", justify="right")

        for scores in scored_offers:
            o = scores.offer
            total = o.total_compensation
            table.add_row(
                o.company,
                f"${o.base_salary:,.0f}",
                f"${o.bonus:,.0f}",
                f"${o.equity // o.equity_years:,.0f}",
                f"${total:,.0f}",
            )

        lines.append(table)
        lines.append("")

        # Weighted scores
        lines.append("## Weighted Scores")
        lines.append("")
        lines.append(
            f"*Using priorities: Salary {self.priorities.salary_weight}%, "
            f"Growth {self.priorities.growth_weight}%, "
            f"WLB {self.priorities.wlb_weight}%, "
            f"Benefits {self.priorities.benefits_weight}%*"
        )
        lines.append("")

        scores_table = Table()
        scores_table.add_column("Company", style="cyan")
        scores_table.add_column("Comp", style="green", justify="right")
        scores_table.add_column("Growth", style="green", justify="right")
        scores_table.add_column("WLB", style="green", justify="right")
        scores_table.add_column("Benefits", style="green", justify="right")
        scores_table.add_column("Weighted", style="yellow", justify="right")

        for scores in scored_offers:
            o = scores.offer
            scores_table.add_row(
                o.company,
                f"{scores.compensation_score:.1f}/10",
                f"{scores.growth_score:.1f}/10",
                f"{scores.wlb_score:.1f}/10",
                f"{scores.benefits_score:.1f}/10",
                f"**{scores.weighted_score:.1f}**/10",
            )

        lines.append(scores_table)
        lines.append("")

        # Recommendation
        if scored_offers:
            winner = scored_offers[0]
            lines.append("## Recommendation")
            lines.append("")
            lines.append(
                f"**{winner.offer.company}** is the top recommendation with a weighted score of **{winner.weighted_score:.1f}/10**."
            )
            lines.append("")

            # Add comparison text
            if len(scored_offers) > 1:
                runner_up = scored_offers[1]
                diff = winner.weighted_score - runner_up.weighted_score
                lines.append(f"It scores {diff:.1f} points higher than {runner_up.offer.company}.")

        return "\n".join(lines)

    def list_offers(self) -> List[Offer]:
        """List all offers."""
        return self.offers

    def clear_offers(self) -> None:
        """Clear all offers."""
        self.offers = []
        self._save_offers()


def add_offer(
    company: str,
    role: str,
    base_salary: float = 0,
    bonus: float = 0,
    equity: float = 0,
    equity_years: int = 4,
    benefits_value: float = 0,
    location: str = "",
    remote: bool = False,
    notes: str = "",
) -> Offer:
    """
    Add a new job offer.

    Args:
        company: Company name
        role: Job role/title
        base_salary: Annual base salary
        bonus: Annual bonus
        equity: Total equity/options value
        equity_years: Years for equity vesting
        benefits_value: Annual benefits value
        location: Job location
        remote: Is remote position
        notes: Additional notes

    Returns:
        Created Offer object
    """
    offer = Offer(
        company=company,
        role=role,
        base_salary=base_salary,
        bonus=bonus,
        equity=equity,
        equity_years=equity_years,
        benefits_value=benefits_value,
        location=location,
        remote=remote,
        notes=notes,
    )

    comparison = OfferComparison()
    comparison.add_offer(offer)

    return offer


def compare_offers() -> List[OfferScores]:
    """
    Compare all stored offers.

    Returns:
        List of scored offers
    """
    comparison = OfferComparison()
    return comparison.compare_offers()


def generate_report() -> str:
    """
    Generate offer comparison report.

    Returns:
        Markdown-formatted report
    """
    comparison = OfferComparison()
    return comparison.generate_comparison_report()


def set_priorities(
    salary: int = 30,
    growth: int = 25,
    wlb: int = 25,
    benefits: int = 20,
) -> None:
    """
    Set priorities for offer comparison.

    Args:
        salary: Weight for salary (0-100)
        growth: Weight for career growth (0-100)
        wlb: Weight for work-life balance (0-100)
        benefits: Weight for benefits (0-100)
    """
    priorities = UserPriorities(
        salary_weight=salary,
        growth_weight=growth,
        wlb_weight=wlb,
        benefits_weight=benefits,
    )
    comparison = OfferComparison()
    comparison.update_priorities(priorities)
