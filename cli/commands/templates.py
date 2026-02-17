"""Template Marketplace - Browse, install, and manage resume templates."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..utils.config import Config
from ..utils.lazy import LazyConsole

console = LazyConsole()

# Default template marketplace registry path
DEFAULT_MARKETPLACE_REGISTRY = Path(__file__).parent.parent.parent / "marketplace" / "registry.json"
DEFAULT_USER_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "user"


class TemplateMetadata:
    """Metadata for a resume template."""

    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        author: str = "unknown",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        rating: float = 0.0,
        reviews_count: int = 0,
        downloads: int = 0,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        source: str = "local",
        source_url: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.author = author
        self.version = version
        self.tags = tags or []
        self.formats = formats or ["md", "tex", "pdf"]
        self.rating = rating
        self.reviews_count = reviews_count
        self.downloads = downloads
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d")
        self.updated_at = updated_at or self.created_at
        self.source = source
        self.source_url = source_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "formats": self.formats,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "downloads": self.downloads,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "source_url": self.source_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            author=data.get("author", "unknown"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            formats=data.get("formats", ["md", "tex", "pdf"]),
            rating=data.get("rating", 0.0),
            reviews_count=data.get("reviews_count", 0),
            downloads=data.get("downloads", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            source=data.get("source", "local"),
            source_url=data.get("source_url"),
        )


class TemplateMarketplace:
    """Template marketplace for browsing, installing, and managing resume templates."""

    CATEGORIES = [
        "professional",
        "modern",
        "minimalist",
        "academic",
        "creative",
        "tech",
        "executive",
        "student",
    ]

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        user_templates_dir: Optional[Path] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize template marketplace.

        Args:
            registry_path: Path to marketplace registry JSON file
            user_templates_dir: Directory for user-installed templates
            config: Configuration object
        """
        self.config = config or Config()
        self.registry_path = registry_path or DEFAULT_MARKETPLACE_REGISTRY
        self.user_templates_dir = user_templates_dir or DEFAULT_USER_TEMPLATES_DIR

        # Ensure directories exist
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)

        # Load registry
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load template registry from file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Return default registry if file is corrupted
                pass

        # Return default registry with built-in templates
        return self._create_default_registry()

    def _create_default_registry(self) -> Dict[str, Any]:
        """Create default registry with built-in templates."""
        return {
            "templates": {
                "resume_md": TemplateMetadata(
                    name="resume_md",
                    description="Standard Markdown resume template with classic formatting",
                    category="professional",
                    author="resume-cli",
                    tags=["markdown", "classic", "ats-friendly"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
                "resume_modern_md": TemplateMetadata(
                    name="resume_modern_md",
                    description="Modern Markdown resume with clean design and minimal borders",
                    category="modern",
                    author="resume-cli",
                    tags=["markdown", "modern", "clean"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
                "resume_minimalist_md": TemplateMetadata(
                    name="resume_minimalist_md",
                    description="Minimalist Markdown resume with focus on content",
                    category="minimalist",
                    author="resume-cli",
                    tags=["markdown", "minimal", "simple"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
                "resume_academic_md": TemplateMetadata(
                    name="resume_academic_md",
                    description="Academic CV template with publications and research focus",
                    category="academic",
                    author="resume-cli",
                    tags=["markdown", "academic", "cv", "publications"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
                "resume_tech_md": TemplateMetadata(
                    name="resume_tech_md",
                    description="Tech-focused resume highlighting skills and projects",
                    category="tech",
                    author="resume-cli",
                    tags=["markdown", "tech", "skills", "projects"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
                "resume_tex": TemplateMetadata(
                    name="resume_tex",
                    description="LaTeX resume template for PDF generation",
                    category="professional",
                    author="resume-cli",
                    tags=["latex", "pdf", "professional"],
                    formats=["tex", "pdf"],
                    source="builtin",
                ).to_dict(),
                "cover_letter_md": TemplateMetadata(
                    name="cover_letter_md",
                    description="Standard cover letter template in Markdown",
                    category="professional",
                    author="resume-cli",
                    tags=["markdown", "cover-letter"],
                    formats=["md"],
                    source="builtin",
                ).to_dict(),
            },
            "categories": self.CATEGORIES,
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
            },
        }

    def _save_registry(self) -> None:
        """Save registry to file."""
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2)

    def list_templates(
        self, category: Optional[str] = None, tag: Optional[str] = None
    ) -> List[TemplateMetadata]:
        """
        List available templates.

        Args:
            category: Filter by category
            tag: Filter by tag

        Returns:
            List of template metadata
        """
        templates = []
        for template_data in self.registry.get("templates", {}).values():
            metadata = TemplateMetadata.from_dict(template_data)

            # Apply filters
            if category and metadata.category != category:
                continue
            if tag and tag not in metadata.tags:
                continue

            templates.append(metadata)

        # Sort by rating (highest first), then by downloads
        templates.sort(key=lambda t: (t.rating, t.downloads), reverse=True)
        return templates

    def get_categories(self) -> List[str]:
        """Get available template categories."""
        return self.registry.get("categories", self.CATEGORIES)

    def get_template(self, name: str) -> Optional[TemplateMetadata]:
        """
        Get template metadata by name.

        Args:
            name: Template name

        Returns:
            Template metadata or None if not found
        """
        template_data = self.registry.get("templates", {}).get(name)
        if template_data:
            return TemplateMetadata.from_dict(template_data)
        return None

    def preview_template(self, name: str, lines: int = 30) -> Optional[str]:
        """
        Preview template content.

        Args:
            name: Template name
            lines: Number of lines to show

        Returns:
            Template content preview or None if not found
        """
        # Check built-in templates
        template_dir = Path(__file__).parent.parent.parent / "templates"
        template_file = template_dir / f"{name}.j2"

        if template_file.exists():
            content = template_file.read_text(encoding="utf-8")
            return "\n".join(content.split("\n")[:lines])

        # Check user templates
        user_template = self.user_templates_dir / f"{name}.j2"
        if user_template.exists():
            content = user_template.read_text(encoding="utf-8")
            return "\n".join(content.split("\n")[:lines])

        return None

    def install_template(
        self,
        source_path: Path,
        name: Optional[str] = None,
        metadata: Optional[TemplateMetadata] = None,
    ) -> Path:
        """
        Install a template from a file.

        Args:
            source_path: Path to template file
            name: Optional template name (defaults to filename)
            metadata: Optional template metadata

        Returns:
            Path to installed template
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Template not found: {source_path}")

        # Determine template name
        if name is None:
            name = source_path.stem

        # Validate template file
        if source_path.suffix != ".j2":
            raise ValueError("Template file must have .j2 extension")

        # Copy to user templates directory
        dest_path = self.user_templates_dir / source_path.name
        shutil.copy2(source_path, dest_path)

        # Register template
        if metadata is None:
            metadata = TemplateMetadata(
                name=name,
                description=f"User-installed template: {name}",
                category="custom",
                author="user",
                source="user",
            )

        self.registry["templates"][name] = metadata.to_dict()
        self.registry["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self._save_registry()

        return dest_path

    def uninstall_template(self, name: str) -> bool:
        """
        Uninstall a user template.

        Args:
            name: Template name

        Returns:
            True if uninstalled, False if template not found or is builtin
        """
        template = self.get_template(name)
        if not template:
            return False

        # Cannot uninstall builtin templates
        if template.source == "builtin":
            raise ValueError(f"Cannot uninstall builtin template: {name}")

        # Remove template file
        template_file = self.user_templates_dir / f"{name}.j2"
        if template_file.exists():
            template_file.unlink()

        # Remove from registry
        del self.registry["templates"][name]
        self._save_registry()

        return True

    def rate_template(self, name: str, rating: float, review: Optional[str] = None) -> bool:
        """
        Rate a template.

        Args:
            name: Template name
            rating: Rating (1.0-5.0)
            review: Optional review text

        Returns:
            True if rated successfully
        """
        if not 1.0 <= rating <= 5.0:
            raise ValueError("Rating must be between 1.0 and 5.0")

        template = self.get_template(name)
        if not template:
            return False

        # Update rating (simple average)
        current_rating = template.rating
        current_reviews = template.reviews_count

        new_rating = ((current_rating * current_reviews) + rating) / (current_reviews + 1)
        template.rating = round(new_rating, 2)
        template.reviews_count += 1

        self.registry["templates"][name] = template.to_dict()
        self._save_registry()

        # Store review if provided
        if review:
            self._add_review(name, review, rating)

        return True

    def _add_review(self, name: str, review: str, rating: float) -> None:
        """Add a review to a template."""
        if "reviews" not in self.registry:
            self.registry["reviews"] = {}

        if name not in self.registry["reviews"]:
            self.registry["reviews"][name] = []

        self.registry["reviews"][name].append(
            {
                "review": review,
                "rating": rating,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        self._save_registry()

    def get_reviews(self, name: str) -> List[Dict[str, Any]]:
        """
        Get reviews for a template.

        Args:
            name: Template name

        Returns:
            List of reviews
        """
        return self.registry.get("reviews", {}).get(name, [])

    def export_template(self, name: str, output_path: Path) -> Path:
        """
        Export a template to a file.

        Args:
            name: Template name
            output_path: Output file path

        Returns:
            Path to exported file
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")

        # Find template file
        template_file = None
        template_dir = Path(__file__).parent.parent.parent / "templates"
        builtin_template = template_dir / f"{name}.j2"
        if builtin_template.exists():
            template_file = builtin_template
        else:
            user_template = self.user_templates_dir / f"{name}.j2"
            if user_template.exists():
                template_file = user_template

        if not template_file:
            raise ValueError(f"Template file not found: {name}")

        # Copy to output path
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_file, output_path)

        # Update download count
        template.downloads += 1
        self.registry["templates"][name] = template.to_dict()
        self._save_registry()

        return output_path

    def search_templates(self, query: str) -> List[TemplateMetadata]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        matches = []

        for template_data in self.registry.get("templates", {}).values():
            metadata = TemplateMetadata.from_dict(template_data)

            # Search in name, description, tags, and category
            searchable = (
                f"{metadata.name} {metadata.description} {' '.join(metadata.tags)} {metadata.category}"
            ).lower()

            if query_lower in searchable:
                matches.append(metadata)

        # Sort by relevance (rating and downloads)
        matches.sort(key=lambda t: (t.rating, t.downloads), reverse=True)
        return matches


@click.group()
def templates():
    """Template marketplace commands."""
    pass


@templates.command("list")
@click.option(
    "-c",
    "--category",
    type=click.Choice(TemplateMarketplace.CATEGORIES + ["custom"]),
    help="Filter by category",
)
@click.option("-t", "--tag", type=str, help="Filter by tag")
@click.pass_context
def list_templates(ctx, category: Optional[str], tag: Optional[str]):
    """List available templates."""
    from rich.table import Table

    marketplace = TemplateMarketplace()

    templates = marketplace.list_templates(category=category, tag=tag)

    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Rating", style="green")
    table.add_column("Downloads", style="blue")

    for template in templates:
        rating_str = f"{'★' * int(template.rating)}{'☆' * (5 - int(template.rating))}"
        table.add_row(
            template.name,
            template.category,
            (
                template.description[:50] + "..."
                if len(template.description) > 50
                else template.description
            ),
            rating_str,
            str(template.downloads),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(templates)} templates[/dim]")


@templates.command("categories")
@click.pass_context
def list_categories(ctx):
    """List template categories."""
    marketplace = TemplateMarketplace()
    categories = marketplace.get_categories()

    console.print("[bold blue]Template Categories[/bold blue]\n")
    for category in categories:
        templates = marketplace.list_templates(category=category)
        console.print(f"  • {category}: {len(templates)} templates")


@templates.command("preview")
@click.argument("name")
@click.option("-l", "--lines", type=int, default=30, help="Number of lines to show")
@click.pass_context
def preview_template(ctx, name: str, lines: int):
    """Preview a template."""
    from rich.panel import Panel

    marketplace = TemplateMarketplace()

    template = marketplace.get_template(name)
    if not template:
        console.print(f"[bold red]Error:[/bold red] Template '{name}' not found")
        return

    # Show metadata
    console.print(f"[bold blue]Template: {name}[/bold blue]")
    console.print(f"  Category: {template.category}")
    console.print(f"  Description: {template.description}")
    console.print(f"  Author: {template.author}")
    console.print(f"  Formats: {', '.join(template.formats)}")
    console.print(f"  Tags: {', '.join(template.tags)}")
    console.print(f"  Rating: {'★' * int(template.rating)} ({template.rating}/5.0)")
    console.print(f"  Downloads: {template.downloads}")

    # Show preview
    content = marketplace.preview_template(name, lines=lines)
    if content:
        console.print(f"\n[bold]Preview (first {lines} lines):[/bold]")
        console.print(Panel(content, border_style="dim"))
    else:
        console.print("[yellow]Could not load template content for preview.[/yellow]")


@templates.command("install")
@click.argument("source", type=click.Path(exists=True))
@click.option("-n", "--name", type=str, help="Template name (defaults to filename)")
@click.option("-d", "--description", type=str, help="Template description")
@click.option(
    "-c",
    "--category",
    type=click.Choice(TemplateMarketplace.CATEGORIES + ["custom"]),
    default="custom",
    help="Template category",
)
@click.pass_context
def install_template(
    ctx, source: str, name: Optional[str], description: Optional[str], category: str
):
    """Install a template from a file."""
    marketplace = TemplateMarketplace()

    try:
        source_path = Path(source)
        metadata = TemplateMetadata(
            name=name or source_path.stem,
            description=description or f"User-installed template: {source_path.stem}",
            category=category,
            author="user",
            source="user",
        )

        installed_path = marketplace.install_template(source_path, name=name, metadata=metadata)

        console.print(f"[green]✓[/green] Template installed: {installed_path}")
        console.print(f"  Name: {metadata.name}")
        console.print(f"  Category: {metadata.category}")

    except Exception as e:
        console.print(f"[bold red]Error installing template:[/bold red] {e}")
        click.get_current_context().exit(1)


@templates.command("uninstall")
@click.argument("name")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def uninstall_template_cmd(ctx, name: str, yes: bool):
    """Uninstall a user template."""
    marketplace = TemplateMarketplace()

    template = marketplace.get_template(name)
    if not template:
        console.print(f"[bold red]Error:[/bold red] Template '{name}' not found")
        click.get_current_context().exit(1)

    if template.source == "builtin":
        console.print(f"[bold red]Error:[/bold red] Cannot uninstall builtin template '{name}'")
        click.get_current_context().exit(1)

    if not yes:
        confirm = click.confirm(f"Are you sure you want to uninstall '{name}'?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            return

    try:
        marketplace.uninstall_template(name)
        console.print(f"[green]✓[/green] Template '{name}' uninstalled")
    except Exception as e:
        console.print(f"[bold red]Error uninstalling template:[/bold red] {e}")
        click.get_current_context().exit(1)


@templates.command("export")
@click.argument("name")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.pass_context
def export_template(ctx, name: str, output: Optional[str]):
    """Export a template to a file."""
    marketplace = TemplateMarketplace()

    try:
        if output is None:
            output = f"{name}.j2"

        output_path = Path(output)
        exported_path = marketplace.export_template(name, output_path)

        console.print(f"[green]✓[/green] Template exported: {exported_path}")

    except Exception as e:
        console.print(f"[bold red]Error exporting template:[/bold red] {e}")
        click.get_current_context().exit(1)


@templates.command("rate")
@click.argument("name")
@click.argument("rating", type=click.FloatRange(1.0, 5.0))
@click.option("-r", "--review", type=str, help="Review text")
@click.pass_context
def rate_template(ctx, name: str, rating: float, review: Optional[str]):
    """Rate a template."""
    marketplace = TemplateMarketplace()

    template = marketplace.get_template(name)
    if not template:
        console.print(f"[bold red]Error:[/bold red] Template '{name}' not found")
        click.get_current_context().exit(1)

    try:
        marketplace.rate_template(name, rating, review=review)
        console.print(f"[green]✓[/green] Rated '{name}': {rating}/5.0")
        if review:
            console.print(f"  Review: {review}")
    except Exception as e:
        console.print(f"[bold red]Error rating template:[/bold red] {e}")
        click.get_current_context().exit(1)


@templates.command("reviews")
@click.argument("name")
@click.pass_context
def show_reviews(ctx, name: str):
    """Show reviews for a template."""
    marketplace = TemplateMarketplace()

    template = marketplace.get_template(name)
    if not template:
        console.print(f"[bold red]Error:[/bold red] Template '{name}' not found")
        click.get_current_context().exit(1)

    reviews = marketplace.get_reviews(name)

    console.print(f"[bold blue]Reviews for '{name}'[/bold blue]")
    console.print(f"  Rating: {'★' * int(template.rating)} ({template.rating}/5.0)")
    console.print(f"  Total reviews: {template.reviews_count}")

    if not reviews:
        console.print("\n[yellow]No reviews yet.[/yellow]")
        return

    console.print("\n")
    for i, review in enumerate(reviews, 1):
        stars = "★" * int(review["rating"]) + "☆" * (5 - int(review["rating"]))
        console.print(f"[bold]{i}. {stars}[/bold] ({review['date']})")
        console.print(f"   {review['review']}")
        console.print()


@templates.command("search")
@click.argument("query")
@click.pass_context
def search_templates(ctx, query: str):
    """Search templates."""
    from rich.table import Table

    marketplace = TemplateMarketplace()

    results = marketplace.search_templates(query)

    if not results:
        console.print(f"[yellow]No templates found matching '{query}'.[/yellow]")
        return

    console.print(f"[bold blue]Search results for '{query}'[/bold blue]\n")

    table = Table()
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Rating", style="green")

    for template in results:
        rating_str = f"{'★' * int(template.rating)}{'☆' * (5 - int(template.rating))}"
        table.add_row(
            template.name,
            template.category,
            (
                template.description[:50] + "..."
                if len(template.description) > 50
                else template.description
            ),
            rating_str,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} templates[/dim]")
