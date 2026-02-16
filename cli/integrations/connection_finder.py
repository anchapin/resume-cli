"""Connection finder for finding alumni/connections at target companies."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Initialize console
console = Console()


@dataclass
class Connection:
    """Represents a professional connection."""

    name: str
    role: str
    company: str
    connection_degree: str  # 1st, 2nd, alumni
    connection_type: str  # linkedin, github, school, previous_company
    common_interests: List[str] = field(default_factory=list)
    profile_url: str = ""
    github_username: str = ""
    school: str = ""
    previous_companies: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    message_suggestion: str = ""


@dataclass
class OutreachSuggestion:
    """Suggested outreach message and talking points."""

    connection: Connection
    message_template: str
    talking_points: List[str] = field(default_factory=list)
    common_ground: str = ""


class ConnectionFinder:
    """Find professional connections at target companies."""

    def __init__(self):
        """Initialize connection finder."""
        self.connections: List[Connection] = []

        # Get user profile info from environment or config
        self.user_school = os.getenv("LINKEDIN_SCHOOL", "")
        self.user_previous_companies = os.getenv("LINKEDIN_PREVIOUS_COMPANIES", "").split(",")

    def find_connections(
        self,
        company: str,
        role: str = "",
        use_linkedin: bool = True,
        use_github: bool = True,
    ) -> List[Connection]:
        """
        Find connections at a target company.

        Args:
            company: Target company name
            role: Optional role/department filter
            use_linkedin: Search LinkedIn connections
            use_github: Search GitHub organization members

        Returns:
            List of Connection objects
        """
        console.print(f"[bold blue]Finding connections at {company}...[/bold blue]")

        connections = []

        # This is a demonstration implementation
        # In production, this would integrate with:
        # - LinkedIn API (requires OAuth)
        # - GitHub API (for org members)
        # - User's existing connection data

        # For demo purposes, show a message about required setup
        if use_linkedin:
            console.print("[yellow]Note:[/yellow] LinkedIn integration requires API credentials.")
            console.print("  Set LINKEDIN_API_KEY environment variable for full functionality.")

        # Search GitHub for company organization
        if use_github:
            connections.extend(self._search_github_org(company, role))

        self.connections = connections
        return connections

    def _search_github_org(self, company: str, role: str = "") -> List[Connection]:
        """Search GitHub for company organization members."""
        connections = []

        # Map common companies to their GitHub organizations
        company_github_orgs = {
            "google": "google",
            "meta": "facebook",
            "facebook": "facebook",
            "amazon": "aws",
            "microsoft": "microsoft",
            "apple": "apple",
            "netflix": "netflix",
            "stripe": "stripe",
            "airbnb": "airbnb",
            "uber": "uber",
            "twitter": "twitter",
            "linkedin": "linkedin",
            "salesforce": "salesforce",
            "adobe": "adobe",
            "github": "github",
        }

        company_lower = company.lower()
        org_name = None
        for name, org in company_github_orgs.items():
            if name in company_lower:
                org_name = org
                break

        if not org_name:
            console.print(f"[dim]No known GitHub organization found for {company}[/dim]")
            return connections

        console.print(f"[dim]Searching GitHub organization: {org_name}...[/dim]")

        # Check if gh CLI is available
        try:
            import subprocess

            result = subprocess.run(
                ["gh", "api", f"orgs/{org_name}/members", "--jq", ".[].login"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout:
                members = result.stdout.strip().split("\n")

                for member in members[:10]:  # Limit to 10 for demo
                    conn = Connection(
                        name=member,
                        role="GitHub Member",
                        company=company,
                        connection_degree="open_source",
                        connection_type="github",
                        profile_url=f"https://github.com/{member}",
                        github_username=member,
                    )
                    connections.append(conn)

                console.print(f"[green]✓[/green] Found {len(connections)} GitHub members")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access GitHub: {e}")

        return connections

    def find_alumni(self, company: str) -> List[Connection]:
        """Find alumni (same school) at a company."""
        if not self.user_school:
            console.print("[yellow]No school configured.[/yellow]")
            console.print("  Set LINKEDIN_SCHOOL environment variable.")
            return []

        console.print(f"[bold]Searching for {self.user_school} alumni at {company}...[/bold]")

        # This would integrate with LinkedIn API in production
        # For demo, return sample data
        connections = []

        # Sample alumni connection
        connections.append(
            Connection(
                name="Sample Alumni",
                role="Senior Engineer",
                company=company,
                connection_degree="alumni",
                connection_type="school",
                school=self.user_school,
                common_interests=["Python", "Machine Learning"],
                message_suggestion=f"Hi! I noticed we're both {self.user_school} alumni. I'd love to connect and learn more about your experience at {company}!",
            )
        )

        return connections

    def find_previous_company_connections(self, company: str) -> List[Connection]:
        """Find people who worked at your previous companies at the target company."""
        if not self.user_previous_companies:
            console.print("[yellow]No previous companies configured.[/yellow]")
            console.print(
                "  Set LINKEDIN_PREVIOUS_COMPANIES environment variable (comma-separated)."
            )
            return []

        connections = []

        for prev_company in self.user_previous_companies:
            if prev_company.strip():
                console.print(
                    f"[dim]Searching for former {prev_company} employees at {company}...[/dim]"
                )

                # Sample connection
                connections.append(
                    Connection(
                        name=f"Former {prev_company} Employee",
                        role="Engineering Manager",
                        company=company,
                        connection_degree="colleague",
                        connection_type="previous_company",
                        previous_companies=[prev_company],
                        common_interests=["Leadership", "Scaling Teams"],
                        message_suggestion=f"Hi! I noticed you worked at {prev_company} - I did too! Would love to connect and share experiences.",
                    )
                )

        return connections

    def generate_outreach_suggestions(
        self,
        connections: List[Connection],
    ) -> List[OutreachSuggestion]:
        """Generate outreach message suggestions for connections."""
        suggestions = []

        for conn in connections:
            # Build message based on connection type
            if conn.connection_degree == "alumni":
                message = f"""Hi {conn.name}!

I noticed we're both alumni of {conn.school}, and I'm very interested in learning more about your experience at {conn.company}.

I'm currently exploring opportunities in the {conn.role} space and would love to connect for a brief chat about how you landed at {conn.company} and what the culture is like.

Would you be open to a 15-minute call? I'd really appreciate any insights you can share!

Best regards"""

            elif conn.connection_degree == "colleague":
                message = f"""Hi {conn.name}!

I see we have a connection through {conn.previous_companies[0]}. I'm currently exploring opportunities at {conn.company} and would love to connect with someone who understands that background.

Would you be available for a quick chat about your experience at {conn.company}? I'd love to learn more about the team and culture.

Thanks for your time!"""

            elif conn.connection_type == "github":
                message = f"""Hi {conn.name}!

I came across your GitHub profile and noticed you're at {conn.company}. I'm a fellow developer interested in your open-source work.

I'm currently exploring opportunities at {conn.company} and would love to connect. Would you be open to a brief conversation about your experience there?

Best regards"""

            else:
                message = f"""Hi {conn.name}!

I'm currently exploring opportunities at {conn.company} and came across your profile. I'd love to connect and learn more about your experience there.

Would you be available for a brief chat? I have some specific questions about the {conn.role} role that I'd appreciate your insights on.

Thank you!"""

            # Build talking points
            talking_points = [
                f"Ask about their experience as {conn.role}",
                "Inquire about team culture and work-life balance",
                "Ask about the hiring process",
                "Get their perspective on growth opportunities",
            ]

            if conn.common_interests:
                talking_points.insert(
                    0, f"Discuss common interests: {', '.join(conn.common_interests)}"
                )

            suggestion = OutreachSuggestion(
                connection=conn,
                message_template=message,
                talking_points=talking_points,
                common_ground=(
                    ", ".join(conn.common_interests)
                    if conn.common_interests
                    else conn.connection_degree
                ),
            )

            suggestions.append(suggestion)

        return suggestions

    def export_to_csv(self, connections: List[Connection], output_path: Path) -> None:
        """Export connections to CSV file."""
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Name", "Role", "Company", "Connection Degree", "Profile URL", "Common Interests"]
            )

            for conn in connections:
                writer.writerow(
                    [
                        conn.name,
                        conn.role,
                        conn.company,
                        conn.connection_degree,
                        conn.profile_url,
                        ", ".join(conn.common_interests),
                    ]
                )

        console.print(f"[green]✓[/green] Exported {len(connections)} connections to {output_path}")

    def print_connections_table(self, connections: List[Connection]) -> None:
        """Print connections in a rich table."""
        if not connections:
            console.print("[yellow]No connections found.[/yellow]")
            return

        table = Table(title=f"Connections Found ({len(connections)})")
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="white")
        table.add_column("Degree", style="yellow")
        table.add_column("Type", style="green")

        for conn in connections:
            table.add_row(
                conn.name,
                conn.role,
                conn.connection_degree,
                conn.connection_type,
            )

        console.print(table)


def find_connections_at_company(
    company: str,
    role: str = "",
    use_linkedin: bool = True,
    use_github: bool = True,
) -> List[Connection]:
    """
    Find connections at a target company.

    Args:
        company: Target company name
        role: Optional role/department filter
        use_linkedin: Search LinkedIn connections
        use_github: Search GitHub organization members

    Returns:
        List of Connection objects
    """
    finder = ConnectionFinder()
    return finder.find_connections(company, role, use_linkedin, use_github)
