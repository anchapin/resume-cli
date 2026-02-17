#!/usr/bin/env python3
"""
Resume CLI System
A unified command-line interface for generating and managing job-specific resumes.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .utils.config import Config
from .utils.yaml_parser import ResumeYAML

# Initialize rich console
console = Console()

# Default paths
DEFAULT_YAML_PATH = Path(__file__).parent.parent / "resume.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default.yaml"


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--yaml-path",
    type=click.Path(),
    default=str(DEFAULT_YAML_PATH),
    help="Path to resume.yaml file",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True),
    default=str(DEFAULT_CONFIG_PATH),
    help="Path to config file",
)
@click.pass_context
def cli(ctx, yaml_path: str, config_path: str):
    """
    Resume CLI System

    Generate job-specific resumes from a single YAML source.
    Supports template-based and AI-powered generation with tracking integration.
    """
    ctx.ensure_object(dict)

    # Load config
    config = Config(Path(config_path) if Path(config_path).exists() else None)

    # Store in context
    ctx.obj["yaml_path"] = Path(yaml_path)
    ctx.obj["config"] = config
    ctx.obj["yaml_handler"] = ResumeYAML(Path(yaml_path))


@cli.command()
@click.option("--from-existing", is_flag=True, help="Initialize from existing resume files")
@click.pass_context
def init(ctx, from_existing: bool):
    """Initialize resume.yaml from existing resume files."""
    from .commands.init import init_from_existing

    job_hunt_dir = Path(__file__).parent.parent

    if from_existing:
        console.print("[bold blue]Initializing resume.yaml from existing files...[/bold blue]")

        try:
            init_from_existing(
                base_resume_path=job_hunt_dir / "resumes" / "base_resume.txt",
                revised_resume_path=job_hunt_dir / "Alex Chapin - Resume - REVISED.md",
                output_path=job_hunt_dir / "resume.yaml",
            )
            console.print("[green]✓[/green] Initialization complete!")
            console.print("  Review and edit resume.yaml as needed.")
        except Exception as e:
            console.print(f"[bold red]Error initializing:[/bold red] {e}")
            sys.exit(1)
    else:
        # Create minimal resume.yaml
        yaml_path = job_hunt_dir / "resume.yaml"
        if yaml_path.exists():
            console.print("[yellow]resume.yaml already exists.[/yellow]")
            console.print("  Use --from-existing to reinitialize from existing files.")
            return

        console.print("[bold blue]Creating minimal resume.yaml...[/bold blue]")
        console.print("[yellow]Edit it manually or use --from-existing flag.[/yellow]")


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate resume.yaml schema and data."""
    # Lazy import for performance
    from .utils.schema import ResumeValidator

    yaml_path = ctx.obj["yaml_path"]

    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init --from-existing' to create it.")
        sys.exit(1)

    console.print("[bold blue]Validating resume.yaml...[/bold blue]")

    validator = ResumeValidator(yaml_path)
    is_valid = validator.validate_all()
    validator.print_results()

    sys.exit(0 if is_valid else 1)


@cli.command()
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to generate")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["md", "tex", "pdf", "txt", "docx"]),
    default="md",
    help="Output format",
)
@click.option(
    "-t",
    "--template",
    type=click.Choice(["base", "modern", "minimalist", "academic", "tech"]),
    default="base",
    help="Resume template style",
)
@click.option(
    "--template-path",
    type=click.Path(exists=True),
    help="Path to custom Jinja2 template file (overrides --template)",
)
@click.option(
    "-o", "--output", type=click.Path(), help="Output file path (default: auto-generated)"
)
@click.option("--no-save", is_flag=True, help="Print to stdout without saving")
@click.option("--ai", is_flag=True, help="Use AI-powered generation (requires API key)")
@click.option(
    "--job-desc",
    type=click.Path(exists=True),
    help="Path to job description file for AI customization",
)
@click.option(
    "--language",
    type=click.Choice(["en", "es", "fr", "de", "pt", "zh", "ja", "ko"]),
    default="en",
    help="Target language for resume generation (requires AI)",
)
@click.pass_context
def generate(
    ctx,
    variant: str,
    format: str,
    template: str,
    template_path: Optional[str],
    output: Optional[str],
    no_save: bool,
    ai: bool,
    job_desc: Optional[str],
    language: str,
):
    """
    Generate resume from template or AI.

    Examples:
        resume-cli generate -v v1.0.0-base -f md
        resume-cli generate -v v1.1.0-backend -f pdf -o my-resume.pdf
        resume-cli generate -t modern -f md
        resume-cli generate --ai --job-desc job-posting.txt
    """
    # Lazy import for performance
    from .generators.template import TemplateGenerator

    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    # Determine template display name
    template_display = template_path if template_path else template
    console.print(f"[bold blue]Generating resume: {variant}[/bold blue]")
    console.print(f"  Format: {format.upper()}")
    console.print(f"  Template: {template_display}")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description if provided
    job_description = None
    if job_desc:
        job_description = Path(job_desc).read_text()

    try:
        # Determine output path
        if output:
            output_path = Path(output)
        else:
            output_path = None

        # Handle custom template path
        custom_template_path = None
        if template_path:
            custom_template_path = Path(template_path)
            console.print(f"  Using custom template: {custom_template_path}")

        # Generate
        if language and language != "en":
            # Multi-language generation
            from .generators.multi_language_generator import MultiLanguageResumeGenerator

            console.print(f"[cyan]Translating resume to {language}...[/cyan]")
            generator = MultiLanguageResumeGenerator(yaml_path, config=config)
            content = generator.generate(
                target_language=language,
                variant=variant,
                output_format=format,
            )

            # Determine output path
            if output_path is None and not no_save:
                base_path = TemplateGenerator(yaml_path, config=config).get_output_path(
                    variant, format
                )
                stem = base_path.stem
                output_path = base_path.parent / f"{stem}-{language}{base_path.suffix}"

            # Save content
            if output_path:
                output_path.write_text(content)
        elif ai or job_description:
            from .generators.ai_generator import AIGenerator

            console.print("[cyan]Using AI-powered generation...[/cyan]")
            generator = AIGenerator(yaml_path, config=config)

            if output_path is None and not no_save:
                # Add -ai suffix to filename
                base_path = TemplateGenerator(yaml_path, config=config).get_output_path(
                    variant, format
                )
                stem = base_path.stem
                output_path = base_path.parent / f"{stem}-ai{base_path.suffix}"

            content = generator.generate(
                variant=variant,
                job_description=job_description,
                output_format=format,
                output_path=output_path,
                custom_template_path=custom_template_path,
            )
        else:
            generator = TemplateGenerator(yaml_path, config=config)

            if output_path is None and not no_save:
                output_path = generator.get_output_path(variant, format)

            # Handle custom template or built-in template selection
            if custom_template_path:
                content = generator.generate(
                    variant=variant,
                    output_format=format,
                    output_path=output_path,
                    custom_template_path=custom_template_path,
                )
            elif template != "base":
                content = generator.generate(
                    variant=variant,
                    output_format=format,
                    output_path=output_path,
                    template=template,
                )
            else:
                content = generator.generate(
                    variant=variant, output_format=format, output_path=output_path
                )

        if no_save:
            console.print("\n" + "-" * 80)
            console.print(content)
            console.print("-" * 80)
        else:
            console.print(f"[green]✓[/green] Generated: {output_path}")

            # Show file size
            if output_path and output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                console.print(f"  Size: {size_kb:.1f} KB")

    except Exception as e:
        console.print(f"[bold red]Error generating resume:[/bold red] {e}")
        sys.exit(1)


@cli.command("generate-package")
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to generate")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["md", "tex", "pdf"]),
    default="md",
    help="Deprecated: generate-package always produces both MD and PDF formats",
)
@click.option(
    "--job-desc", type=click.Path(exists=True), required=True, help="Path to job description file"
)
@click.option(
    "--company", type=str, help="Company name (overrides extraction from job description)"
)
@click.option("--non-interactive", is_flag=True, help="Skip questions, use smart defaults")
@click.option("--no-cover-letter", is_flag=True, help="Skip cover letter generation")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: config setting)")
@click.option(
    "--include-github-projects",
    is_flag=True,
    help="Auto-select and include GitHub projects matching job technologies (searches repos AND code in organization)",
)
@click.pass_context
def generate_package(
    ctx,
    variant: str,
    format: str,
    job_desc: str,
    company: Optional[str],
    non_interactive: bool,
    no_cover_letter: bool,
    output_dir: Optional[str],
    include_github_projects: bool,
):
    """
    Generate a complete application package: resume + cover letter.

    Output is organized in subdirectories:
        output/{company}-{date}/
            ├── resume.md
            ├── resume.pdf
            ├── cover-letter.md
            └── cover-letter.pdf

    Both resume and cover letter are generated in MD and PDF formats.

    Examples:
        resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend
        resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive
        resume-cli generate-package --job-desc job.txt --variant v1.2.0-ml_ai
    """
    import re
    from datetime import datetime

    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print("[bold blue]Generating Application Package[/bold blue]")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description
    job_description = Path(job_desc).read_text()

    # Determine output directory
    if output_dir:
        output_base_dir = Path(output_dir)
    else:
        output_base_dir = config.output_dir

    output_base_dir = Path(output_base_dir)
    output_base_dir.mkdir(parents=True, exist_ok=True)

    # Generate outputs
    all_saved_paths = {}

    try:
        # Step 1: Generate AI-customized resume (both MD and PDF)
        console.print("\n[cyan]Step 1: Generating AI-customized resume...[/cyan]")
        from .generators.ai_generator import AIGenerator

        resume_gen = AIGenerator(yaml_path, config=config)

        # For package output, we need to determine the company name first
        # Extract company name for directory structure
        from .generators.cover_letter_generator import CoverLetterGenerator

        cl_gen_temp = CoverLetterGenerator(yaml_path, config=config)
        job_details_temp = cl_gen_temp._extract_job_details(job_description, company)
        company_name = company or job_details_temp.get("company", "company")

        # Create package directory
        date_str = datetime.now().strftime("%Y-%m-%d")
        company_slug = re.sub(r"[^\w\s-]", "", company_name).strip().lower()[:30]
        company_slug = re.sub(r"[-\s]+", "-", company_slug)
        package_dir = output_base_dir / f"{company_slug}-{date_str}"
        package_dir.mkdir(parents=True, exist_ok=True)

        # Step 1.5: Auto-select GitHub projects if requested
        enhanced_context = {}
        if include_github_projects:
            console.print(
                "\n[cyan]Step 1.5: Selecting GitHub projects matching job technologies...[/cyan]"
            )
            try:
                from .integrations.github_sync import GitHubSync

                # Extract technologies from job description using AI
                technologies = resume_gen.extract_technologies(job_description)

                if not technologies:
                    console.print(
                        "[yellow]Warning:[/yellow] No technologies extracted from job description."
                    )
                    console.print("  Continuing without GitHub projects.")
                else:
                    console.print(f"[dim]Extracted technologies: {', '.join(technologies)}[/dim]")
                    console.print(
                        f"[dim]Using top 3 for matching: {', '.join(technologies[:3])}[/dim]"
                    )
                    console.print("[dim]Searching for code in organization...[/dim]")

                    # Select matching projects
                    github_sync = GitHubSync(config)
                    max_projects = config.get("github.max_projects", 3)
                    months = config.get("github.sync_months", 12)

                    selected_projects = github_sync.select_matching_projects(
                        technologies=technologies, top_n=max_projects, months=months
                    )

                    if not selected_projects:
                        top_techs = technologies[:3]
                        console.print(
                            f"[yellow]Warning:[/yellow] No matching GitHub projects found for: {', '.join(top_techs)}"
                        )
                        console.print("  Continuing without GitHub projects.")
                    else:
                        console.print(
                            f"[green]✓[/green] Selected {len(selected_projects)} GitHub projects:"
                        )
                        for proj in selected_projects:
                            console.print(
                                f"    • {proj['name']} ({proj['language']}) - score: {proj['match_score']}"
                            )

                        # Enhance project descriptions with AI (ephemeral - doesn't modify resume.yaml)
                        enhanced_projects = resume_gen.enhance_project_descriptions(
                            projects=selected_projects,
                            job_description=job_description,
                            technologies=technologies,
                        )

                        # Generate enhanced professional summary integrating projects
                        base_summary = ctx.obj["yaml_handler"].get_summary(variant)
                        enhanced_summary = resume_gen.generate_project_summary(
                            enhanced_projects=enhanced_projects,
                            base_summary=base_summary,
                            variant=variant,
                        )

                        # Build enhanced context for template rendering
                        enhanced_context = {
                            "projects": {"featured": enhanced_projects},
                            "summary": enhanced_summary,
                        }

                        console.print(
                            "[dim]AI enhancements applied (ephemeral - resume.yaml unchanged)[/dim]"
                        )

            except RuntimeError as e:
                console.print(f"[yellow]Warning:[/yellow] GitHub CLI error: {e}")
                console.print(
                    "  Continuing without GitHub projects. Make sure 'gh' CLI is installed and authenticated."
                )
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Failed to select GitHub projects: {e}")
                console.print("  Continuing without GitHub projects.")

        # Generate resume in both MD and PDF formats
        resume_formats = ["md", "pdf"]
        for resume_format in resume_formats:
            resume_path = package_dir / f"resume.{resume_format}"
            resume_gen.generate(
                variant=variant,
                job_description=job_description,
                output_format=resume_format,
                output_path=resume_path,
                enhanced_context=enhanced_context if enhanced_context else None,
            )
            all_saved_paths[f"resume_{resume_format}"] = resume_path
            console.print(f"[green]✓[/green] Resume ({resume_format.upper()}): {resume_path}")

        # Step 2: Generate cover letter
        if not no_cover_letter:
            console.print("\n[cyan]Step 2: Generating cover letter...[/cyan]")

            if non_interactive:
                cover_letter_outputs, job_details = cl_gen_temp.generate_non_interactive(
                    job_description=job_description,
                    company_name=company,
                    variant=variant,
                    output_formats=config.cover_letter_formats,
                )
            else:
                cover_letter_outputs, job_details = cl_gen_temp.generate_interactive(
                    job_description=job_description,
                    company_name=company,
                    variant=variant,
                    output_formats=config.cover_letter_formats,
                )

            # Save cover letter outputs
            cover_letter_paths = cl_gen_temp.save_outputs(
                outputs=cover_letter_outputs, company_name=company_name, output_dir=package_dir
            )

            all_saved_paths.update(cover_letter_paths)

            for fmt, path in cover_letter_paths.items():
                console.print(f"[green]✓[/green] Cover letter ({fmt.upper()}): {path}")

        # Summary
        console.print("\n[bold green]Application package complete![/bold green]")
        console.print(f"[cyan]Package directory:[/cyan] {package_dir}")
        console.print("\n[cyan]Generated files:[/cyan]")
        for name, path in all_saved_paths.items():
            console.print(f"  • {name}: {path}")

    except Exception as e:
        console.print(f"[bold red]Error generating package:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def variants(ctx):
    """List available resume variants."""
    yaml_handler = ctx.obj["yaml_handler"]

    try:
        all_variants = yaml_handler.get_variants()

        table = Table(title="Resume Variants")
        table.add_column("Variant", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Summary", style="yellow")
        table.add_column("Skills", style="green")

        for name, config in all_variants.items():
            skills = ", ".join(config.get("skill_sections", []))
            summary = config.get("summary_key", "base")

            table.add_row(name, config.get("description", ""), summary, skills)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error loading variants:[/bold red] {e}")
        sys.exit(1)


@cli.group()
def track():
    """Application tracking commands."""
    pass


@cli.command()
@click.argument("company")
@click.argument("status")
@click.option("-r", "--role", help="Job role/title")
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant used")
@click.option("-s", "--source", default="manual", help="Application source")
@click.option("-u", "--url", help="Job posting URL")
@click.option("-n", "--notes", help="Additional notes")
@click.pass_context
def apply(
    ctx,
    company: str,
    status: str,
    role: Optional[str],
    variant: str,
    source: str,
    url: Optional[str],
    notes: Optional[str],
):
    """
    Log a job application.

    Examples:
        resume-cli apply AcmeCorp applied -r "Senior Engineer"
        resume-cli apply Google interview -v v1.1.0-backend -s LinkedIn
    """
    from .integrations.tracking import TrackingIntegration

    config = ctx.obj["config"]

    if not config.tracking_enabled:
        console.print("[yellow]Tracking is disabled in config.[/yellow]")
        sys.exit(0)

    try:
        tracker = TrackingIntegration(config)
        tracker.log_application(
            company=company,
            role=role or "Software Engineer",
            status=status,
            variant=variant,
            source=source,
            url=url,
            notes=notes,
        )

        console.print(f"[green]✓[/green] Logged application: {company}")

    except Exception as e:
        console.print(f"[bold red]Error logging application:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--months", type=int, default=3, help="Number of months to look back")
@click.option("--write", is_flag=True, help="Write projects to resume.yaml (not just preview)")
@click.option("--no-backup", is_flag=True, help="Skip creating backup file (use with --write)")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing (default behavior)")
@click.pass_context
def sync_github(ctx, months: int, write: bool, no_backup: bool, dry_run: bool):
    """Sync GitHub projects to resume.yaml.

    Examples:
        resume-cli sync-github --months 3           # Preview projects (default)
        resume-cli sync-github --months 3 --write   # Auto-update resume.yaml
        resume-cli sync-github --months 6 --dry-run  # Explicit preview mode
    """
    from .integrations.github_sync import GitHubSync

    config = ctx.obj["config"]
    yaml_handler = ctx.obj["yaml_handler"]
    yaml_path = ctx.obj["yaml_path"]

    console.print(f"[bold blue]Syncing GitHub projects (past {months} months)...[/bold blue]")

    # Validate write mode
    if write and not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    try:
        sync = GitHubSync(config)
        projects = sync.fetch_projects(months=months)

        total_projects = sum(len(proj_list) for proj_list in projects.values())
        console.print(f"[green]✓[/green] Found {total_projects} projects")

        # If dry-run (default) or no write flag, just show preview
        if not write or dry_run:
            console.print("\n[bold]Fetched projects by category:[/bold]")
            for category, proj_list in projects.items():
                if proj_list:
                    console.print(f"  {category}: {len(proj_list)} projects")
                    for proj in proj_list[:3]:  # Show first 3
                        console.print(f"    - {proj['name']} ({proj['language']})")
                    if len(proj_list) > 3:
                        console.print(f"    ... and {len(proj_list) - 3} more")

            if dry_run or not write:
                console.print("\n[yellow]Note:[/yellow] This is a preview (--dry-run is default).")
                console.print("  Use --write to update resume.yaml:")
                console.print("    resume-cli sync-github --months 3 --write")
            return

        # Write mode: update resume.yaml
        console.print("\n[bold blue]Updating resume.yaml...[/bold blue]")

        # Create backup if requested
        backup_path = None
        if not no_backup:
            backup_path = yaml_path.with_suffix(".yaml.bak")
            import shutil

            shutil.copy2(yaml_path, backup_path)
            console.print(f"[dim]Created backup: {backup_path}[/dim]")

        # Get existing projects to avoid duplicates
        existing_projects = yaml_handler.get_projects()

        # Flatten existing project names for deduplication
        existing_names = set()
        for category_projects in existing_projects.values():
            if isinstance(category_projects, list):
                for proj in category_projects:
                    if isinstance(proj, dict) and "name" in proj:
                        existing_names.add(proj["name"])

        # Filter out duplicates and prepare new projects
        new_projects_added = 0
        for category, proj_list in projects.items():
            filtered_list = []
            for proj in proj_list:
                if proj["name"] not in existing_names:
                    filtered_list.append(proj)
                    existing_names.add(proj["name"])  # Add to avoid dupes within new projects
                    new_projects_added += 1

            # Update category with filtered list (only new projects)
            if filtered_list:
                if category not in existing_projects:
                    existing_projects[category] = []
                # Extend existing category with new projects
                if isinstance(existing_projects[category], list):
                    existing_projects[category].extend(filtered_list)

        # Save updated YAML
        data = yaml_handler.load()
        data["projects"] = existing_projects
        yaml_handler.save(data)

        console.print(
            f"[green]✓[/green] Updated resume.yaml with {new_projects_added} new projects"
        )

        if backup_path:
            console.print(f"[dim]Backup saved to: {backup_path}[/dim]")

        console.print(
            "\n[bold green]Done![/bold green] Run 'resume-cli variants' to see updated projects."
        )

    except Exception as e:
        console.print(f"[bold red]Error syncing GitHub:[/bold red] {e}")
        console.print("  Make sure 'gh' CLI is installed and authenticated.")
        sys.exit(1)


@cli.command()
@click.option(
    "--days", type=int, default=90, help="Number of days to show in timeline (default: 90)"
)
@click.option(
    "--top-companies", type=int, default=5, help="Number of top companies to show (default: 5)"
)
@click.option("--simple", is_flag=True, help="Show simple statistics only (no charts)")
@click.pass_context
def analyze(ctx, days: int, top_companies: int, simple: bool):
    """
    Show application tracking analytics dashboard.

    Displays a visual dashboard with charts and metrics for job application tracking.

    Examples:
        resume-cli analyze
        resume-cli analyze --days 30
        resume-cli analyze --top-companies 10
        resume-cli analyze --simple
    """
    from .integrations.tracking import TrackingIntegration

    config = ctx.obj["config"]

    if not config.tracking_enabled:
        console.print("[yellow]Tracking is disabled in config.[/yellow]")
        sys.exit(0)

    try:
        tracker = TrackingIntegration(config)
        dashboard_data = tracker.get_dashboard_data()

        # Check if there's any data
        overview = dashboard_data.get("overview", {})
        if overview.get("total_applications", 0) == 0:
            console.print("\n[yellow]No tracking data found.[/yellow]")
            console.print("  Start tracking with: [bold]resume-cli apply <company> <status>[/bold]")
            return

        console.print("\n" + "=" * 80)
        console.print("[bold blue]APPLICATION TRACKING DASHBOARD[/bold blue]")
        console.print("=" * 80)

        if simple:
            # Simple mode - just basic stats
            _print_simple_stats(console, dashboard_data)
        else:
            # Full dashboard
            _print_overview_gauges(console, dashboard_data)
            _print_status_breakdown(console, dashboard_data)
            _print_variant_performance(console, dashboard_data)
            _print_source_breakdown(console, dashboard_data)
            _print_top_companies(console, dashboard_data, limit=top_companies)
            _print_timeline_summary(console, dashboard_data, days=days)

        console.print("\n" + "=" * 80)
        console.print("[dim]Tip: Use --simple for basic stats, --days N for timeline range[/dim]")
        console.print("=" * 80 + "\n")

    except FileNotFoundError:
        console.print("[yellow]No tracking data found.[/yellow]")
        console.print("  Start tracking with: resume-cli apply <company> <status>")
    except Exception as e:
        console.print(f"[bold red]Error analyzing:[/bold red] {e}")
        sys.exit(1)


def _print_simple_stats(console, dashboard_data: dict):
    """Print simple statistics table."""
    overview = dashboard_data.get("overview", {})
    by_status = dashboard_data.get("by_status", {})

    console.print("\n[bold blue]Application Statistics[/bold blue]\n")

    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Applications", str(overview.get("total_applications", 0)))
    table.add_row("Applied", str(by_status.get("applied", 0)))
    table.add_row("Interviews", str(by_status.get("interview", 0)))
    table.add_row("Offers", str(by_status.get("offer", 0)))
    table.add_row("Response Rate", f"{overview.get('response_rate', 0):.1f}%")

    console.print(table)


def _print_overview_gauges(console, dashboard_data: dict):
    """Print overview metrics as gauge-style display."""
    overview = dashboard_data.get("overview", {})

    console.print("\n[bold]📊 Overview Metrics[/bold]\n")

    # Create gauge-style display
    total = overview.get("total_applications", 0)

    # Response Rate Gauge
    response_rate = overview.get("response_rate", 0)
    response_bar = _create_progress_bar(response_rate, width=30)
    console.print(f"  Response Rate:  {response_bar} {response_rate:.1f}%")

    # Interview Rate Gauge
    interview_rate = overview.get("interview_rate", 0)
    interview_bar = _create_progress_bar(interview_rate, width=30)
    console.print(f"  Interview Rate: {interview_bar} {interview_rate:.1f}%")

    # Offer Rate Gauge
    offer_rate = overview.get("offer_rate", 0)
    offer_bar = _create_progress_bar(offer_rate, width=30)
    console.print(f"  Offer Rate:     {offer_bar} {offer_rate:.1f}%")

    console.print(
        f"\n  [dim]Total Applications: {total} | Interviews: {overview.get('interviews', 0)} | Offers: {overview.get('offers', 0)}[/dim]"
    )


def _create_progress_bar(percentage: float, width: int = 30) -> str:
    """Create a text-based progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled

    # Color based on percentage
    if percentage >= 50:
        color = "green"
    elif percentage >= 25:
        color = "yellow"
    else:
        color = "red"

    bar = f"[{color}]{'█' * filled}[/{'green' if percentage >= 50 else 'yellow' if percentage >= 25 else 'red'}]"
    bar += f"[dim]{'░' * empty}[/dim]"
    return bar


def _print_status_breakdown(console, dashboard_data: dict):
    """Print applications by status as a visual breakdown."""
    by_status = dashboard_data.get("by_status", {})

    if not by_status:
        return

    console.print("\n[bold]📋 Applications by Status[/bold]\n")

    total = sum(by_status.values())
    if total == 0:
        return

    # Status icons and colors
    status_config = {
        "applied": ("⏳", "cyan"),
        "interview": ("📞", "yellow"),
        "offer": ("🎉", "green"),
        "rejected": ("❌", "red"),
        "withdrawn": ("🔙", "dim"),
    }

    table = Table(show_header=False, box=None)
    table.add_column("Icon", style="white")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")

    for status, count in sorted(by_status.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        icon, color = status_config.get(status, ("❓", "white"))
        table.add_row(icon, status.capitalize(), str(count), f"{percentage:.1f}%")

    console.print(table)


def _print_variant_performance(console, dashboard_data: dict):
    """Print variant performance comparison."""
    variants = dashboard_data.get("variant_performance", [])

    if not variants:
        return

    console.print("\n[bold]🎯 Variant Performance[/bold]\n")

    table = Table(title="Resume Variant Comparison")
    table.add_column("Variant", style="cyan", no_wrap=True)
    table.add_column("Applications", style="white", justify="right")
    table.add_column("Response Rate", style="green", justify="right")
    table.add_column("Interview Rate", style="yellow", justify="right")
    table.add_column("Offer Rate", style="blue", justify="right")

    for variant in variants:
        table.add_row(
            variant.get("variant", "unknown"),
            str(variant.get("total_applications", 0)),
            f"{variant.get('response_rate', 0):.1f}%",
            f"{variant.get('interview_rate', 0):.1f}%",
            f"{variant.get('offer_rate', 0):.1f}%",
        )

    console.print(table)


def _print_source_breakdown(console, dashboard_data: dict):
    """Print application sources breakdown."""
    sources = dashboard_data.get("source_breakdown", [])

    if not sources:
        return

    console.print("\n[bold]📮 Application Sources[/bold]\n")

    total = sum(s.get("count", 0) for s in sources)
    if total == 0:
        return

    table = Table(show_header=False, box=None)
    table.add_column("Source", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")

    for source in sources[:5]:  # Top 5 sources
        count = source.get("count", 0)
        percentage = (count / total * 100) if total > 0 else 0
        table.add_row(source.get("source", "unknown"), str(count), f"{percentage:.1f}%")

    console.print(table)


def _print_top_companies(console, dashboard_data: dict, limit: int = 5):
    """Print top companies by applications."""
    companies = dashboard_data.get("company_analytics", [])

    if not companies:
        return

    console.print(f"\n[bold]🏢 Top {limit} Companies[/bold]\n")

    table = Table(title=f"Top {limit} Companies by Applications")
    table.add_column("Company", style="cyan")
    table.add_column("Applications", style="green", justify="right")
    table.add_column("Latest Role", style="white")
    table.add_column("Status", style="yellow")

    for company in companies[:limit]:
        # Get most common status
        statuses = company.get("statuses", {})
        top_status = max(statuses.items(), key=lambda x: x[1])[0] if statuses else "unknown"

        # Get latest role
        roles = company.get("roles", [])
        latest_role = roles[0] if roles else "Unknown"

        table.add_row(
            company.get("company", "Unknown"),
            str(company.get("total_applications", 0)),
            latest_role[:25],
            top_status.capitalize(),
        )

    console.print(table)


def _print_timeline_summary(console, dashboard_data: dict, days: int = 90):
    """Print timeline summary with weekly aggregates."""
    timeline = dashboard_data.get("timeline", [])

    if not timeline:
        return

    console.print(f"\n[bold]📈 Application Timeline (Last {days} Days)[/bold]\n")

    # Aggregate by week
    from datetime import datetime

    weekly_counts = {}
    for entry in timeline:
        try:
            date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
            # Get ISO week
            year, week, _ = date.isocalendar()
            week_key = f"{year}-W{week:02d}"
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + entry.get("count", 0)
        except (ValueError, TypeError):
            continue

    if not weekly_counts:
        return

    # Show last 8 weeks
    weeks = list(weekly_counts.items())[-8:]

    # Find max for scaling
    max_count = max(count for _, count in weeks) if weeks else 1

    for week, count in weeks:
        bar_length = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_length
        console.print(f"  {week}: [green]{bar}[/green] [dim]({count})[/dim]")

    # Total for period
    total_in_period = sum(count for _, count in weeks)
    console.print(f"\n  [dim]Total applications in period: {total_in_period}[/dim]")


# Add LinkedIn commands
from .commands.linkedin import linkedin_export, linkedin_import

cli.add_command(linkedin_import)
cli.add_command(linkedin_export)

# Add tutorial command
from .commands.tutorials import tutorial as tutorial_group

cli.add_command(tutorial_group, name="tutorial")

# Add template marketplace commands
from .commands.templates import templates as templates_group

cli.add_command(templates_group, name="templates")

# Add convert commands for JSON Resume interoperability
from .commands.convert import convert, import_json_resume, export_json_resume

cli.add_command(convert)
cli.add_command(import_json_resume, name="import-json-resume")
cli.add_command(export_json_resume, name="export-json-resume")


@cli.command("ats-check")
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to check")
@click.option(
    "--job-desc", type=click.Path(exists=True), required=True, help="Path to job description file"
)
@click.option("--output", type=click.Path(), help="Save report as JSON file")
@click.pass_context
def ats_check(ctx, variant: str, job_desc: str, output: Optional[str]):
    """
    Check ATS (Applicant Tracking System) compatibility score.

    Analyzes resume against job description and provides an ATS score with
    actionable feedback for optimization.

    Examples:
        resume-cli ats-check -v v1.1.0-backend --job-desc job-posting.txt
        resume-cli ats-check --job-desc job.txt --output ats-report.json
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print("[bold blue]Checking ATS Compatibility[/bold blue]")
    console.print(f"  Variant: {variant}")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description
    job_description = Path(job_desc).read_text()
    console.print(f"  Job description: {job_desc}")

    try:
        from .generators.ats_generator import ATSGenerator

        # Generate ATS report
        generator = ATSGenerator(yaml_path, config=config)
        report = generator.generate_report(job_description, variant)

        # Print report
        generator.print_report(report)

        # Export to JSON if requested
        if output:
            output_path = Path(output)
            generator.export_json(report, output_path)
            console.print(f"[green]✓[/green] Report saved to: {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error checking ATS score:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("diff")
@click.argument("variant1", required=False, default="v1.0.0-base")
@click.argument("variant2", required=False, default=None)
@click.option("--all", "show_all", is_flag=True, help="Compare all variants")
@click.option("-o", "--output", type=click.Path(), help="Save diff report to file")
@click.pass_context
def diff(ctx, variant1: str, variant2: Optional[str], show_all: bool, output: Optional[str]):
    """
    Compare resume variants and show differences.

    Examples:
        resume-cli diff v1.0.0-base v1.1.0-backend
        resume-cli diff v1.0.0-base v1.2.0-ml_ai -o diff-report.md
        resume-cli diff --all
    """
    from difflib import unified_diff

    from .generators.template import TemplateGenerator

    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]
    yaml_handler = ctx.obj["yaml_handler"]

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Get available variants
    available_variants = yaml_handler.list_variants()

    if show_all:
        # Compare all variants with base
        variants_to_compare = [v for v in available_variants if v != "v1.0.0-base"]
        base_variant = "v1.0.0-base"
    elif variant2 is None:
        # If only one variant provided, compare with base
        variants_to_compare = [variant1]
        base_variant = "v1.0.0-base"
    else:
        # Compare two specific variants
        variants_to_compare = [variant2]
        base_variant = variant1

    # Validate variants exist
    all_variants_to_check = list(set([base_variant] + variants_to_compare))
    for v in all_variants_to_check:
        if v not in available_variants:
            console.print(f"[bold red]Error:[/bold red] Variant '{v}' not found.")
            console.print(f"  Available variants: {', '.join(available_variants)}")
            sys.exit(1)

    console.print("[bold blue]Comparing Resume Variants[/bold blue]\n")

    try:
        generator = TemplateGenerator(yaml_path, config=config)
        diff_output = []

        for compare_variant in variants_to_compare:
            console.print(f"[cyan]Comparing:[/cyan] {base_variant} → {compare_variant}")

            # Generate content for both variants
            content1 = generator.generate(
                variant=base_variant, output_format="md", output_path=None
            )
            content2 = generator.generate(
                variant=compare_variant, output_format="md", output_path=None
            )

            # Generate unified diff
            lines1 = content1.splitlines(keepends=True)
            lines2 = content2.splitlines(keepends=True)

            diff = unified_diff(
                lines1, lines2, fromfile=f"{base_variant}", tofile=f"{compare_variant}", lineterm=""
            )

            diff_text = "".join(diff)

            if diff_text:
                diff_output.append(f"\n## Diff: {base_variant} → {compare_variant}\n")
                diff_output.append(diff_text)

                console.print("[green]✓[/green] Found differences")
            else:
                diff_output.append(f"\n## Diff: {base_variant} → {compare_variant}\n")
                diff_output.append("No differences found.\n")
                console.print("[yellow]No differences found[/yellow]")

        # Output results
        final_output = "".join(diff_output)

        if output:
            output_path = Path(output)
            output_path.write_text(final_output)
            console.print(f"\n[green]✓[/green] Diff saved to: {output_path}")
        else:
            console.print("\n" + final_output)

    except Exception as e:
        console.print(f"[bold red]Error generating diff:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("keyword-analysis")
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to analyze")
@click.option(
    "--job-desc", type=click.Path(exists=True), required=True, help="Path to job description file"
)
@click.option("--output", type=click.Path(), help="Save report as JSON file")
@click.pass_context
def keyword_analysis(ctx, variant: str, job_desc: str, output: Optional[str]):
    """
    Analyze keyword density between resume and job description.

    Shows which keywords from the job posting are present in your resume
    and provides suggestions for improvement.

    Examples:
        resume-cli keyword-analysis -v v1.1.0-backend --job-desc job-posting.txt
        resume-cli keyword-analysis --job-desc job.txt --output keyword-report.json
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print("[bold blue]Keyword Density Analysis[/bold blue]")
    console.print(f"  Variant: {variant}")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description
    job_description = Path(job_desc).read_text()
    console.print(f"  Job description: {job_desc}")

    try:
        from .utils.keyword_density import KeywordDensityGenerator

        # Generate keyword density report
        generator = KeywordDensityGenerator(yaml_path, config=config)
        report = generator.generate_report(job_description, variant)

        # Print report
        generator.print_report(report)

        # Export to JSON if requested
        if output:
            output_path = Path(output)
            generator.export_json(report, output_path)
            console.print(f"[green]✓[/green] Report saved to: {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error analyzing keywords:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("video-script")
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to use")
@click.option(
    "--job-desc", type=click.Path(exists=True), help="Path to job description file for targeting"
)
@click.option("--company", type=str, help="Target company name")
@click.option(
    "--duration",
    type=click.Choice(["60", "120", "300"]),
    default="60",
    help="Video duration in seconds (60=1min, 120=2min, 300=5min)",
)
@click.option("-o", "--output", type=click.Path(), help="Output file path (default: stdout)")
@click.option(
    "--format",
    type=click.Choice(["markdown", "teleprompter"]),
    default="markdown",
    help="Output format",
)
@click.pass_context
def video_script(
    ctx,
    variant: str,
    job_desc: Optional[str],
    company: Optional[str],
    duration: str,
    output: Optional[str],
    format: str,
):
    """
    Generate a video resume script with visual suggestions and teleprompter text.

    Creates a personalized script for video introductions (60s, 2min, or 5min)
    based on your resume and optional job description.

    Examples:
        resume-cli video-script --variant v1.1.0-backend
        resume-cli video-script --job-desc job-posting.txt --company "Stripe" --duration 120
        resume-cli video-script --job-desc job.txt --format teleprompter -o script.txt
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print("[bold blue]Video Resume Script Generator[/bold blue]")
    console.print(f"  Variant: {variant}")
    console.print(f"  Duration: {duration} seconds")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description if provided
    job_description = ""
    if job_desc:
        job_description = Path(job_desc).read_text()
        console.print(f"  Job description: {job_desc}")

    if company:
        console.print(f"  Target company: {company}")

    try:
        from .generators.video_resume_generator import VideoResumeGenerator

        # Generate video script
        generator = VideoResumeGenerator(yaml_path, config=config)
        script = generator.generate(
            job_description=job_description,
            variant=variant,
            duration=int(duration),
            company_name=company or "",
        )

        # Render to selected format
        if format == "teleprompter":
            content = generator.render_to_teleprompter(script)
        else:
            content = generator.render_to_markdown(script)

        # Output
        if output:
            output_path = Path(output)
            output_path.write_text(content)
            console.print(f"\n[green]✓[/green] Script saved to: {output_path}")
        else:
            console.print("\n" + content)

    except ImportError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("  Install AI dependencies: pip install 'resume-cli[ai]'")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error generating video script:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("mock-interview")
@click.option(
    "--job-desc", type=click.Path(exists=True), required=True, help="Path to job description file"
)
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to use")
@click.option(
    "--category",
    type=click.Choice(["technical", "behavioral", "mixed"]),
    default="mixed",
    help="Interview question category",
)
@click.option("--num-technical", type=int, default=5, help="Number of technical questions")
@click.option("--num-behavioral", type=int, default=3, help="Number of behavioral questions")
@click.option("--no-system-design", is_flag=True, help="Exclude system design questions")
@click.option("-o", "--output", type=click.Path(), help="Save session report to file")
@click.pass_context
def mock_interview(
    ctx,
    job_desc: str,
    variant: str,
    category: str,
    num_technical: int,
    num_behavioral: int,
    no_system_design: bool,
    output: Optional[str],
):
    """
    Start an interactive mock interview session with AI evaluation.

    The session generates interview questions based on the job description and your resume.
    You answer questions and receive AI-powered feedback and evaluation.

    Examples:
        resume-cli mock-interview --job-desc job-posting.txt
        resume-cli mock-interview --job-desc job.txt --category technical --num-technical 8
        resume-cli mock-interview --job-desc job.txt --no-system-design -o report.md
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print("[bold blue]Mock Interview Mode[/bold blue]")
    console.print(f"  Variant: {variant}")
    console.print(f"  Category: {category}")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description
    job_description = Path(job_desc).read_text()
    console.print(f"  Job description: {job_desc}")

    try:
        from .generators.mock_interview_generator import MockInterviewGenerator

        # Start interview session
        generator = MockInterviewGenerator(yaml_path, config=config)
        session = generator.start_session(
            job_description=job_description,
            variant=variant,
            category=category,
            num_technical=num_technical,
            num_behavioral=num_behavioral,
            include_system_design=not no_system_design,
        )

        console.print(f"\n[green]✓[/green] Session ID: {session.session_id}")
        console.print(f"  Total questions: {len(session.questions)}")
        console.print("\n[bold]Instructions:[/bold]")
        console.print("  This is a non-interactive preview mode.")
        console.print(
            "  To use the full interactive mode, run with a terminal that supports input."
        )
        console.print("  For now, we'll show the questions and generate a report.\n")

        # Display questions
        for i, q in enumerate(session.questions[:5], 1):  # Show first 5
            console.print(f"[cyan]Q{i}:[/cyan] {q.get('question', '')}")
            console.print(
                f"  [dim]Type: {q.get('type', 'N/A')} | Priority: {q.get('priority', 'medium')}[/dim]"
            )
            console.print("")

        if len(session.questions) > 5:
            console.print(f"[dim]... and {len(session.questions) - 5} more questions[/dim]")

        # Complete session (for demo purposes, simulate completing with questions displayed)
        summary = generator.complete_session(session)

        console.print("\n[bold green]Session Complete![/bold green]")
        console.print(f"  Questions: {summary['answered']} / {summary['total_questions']}")
        console.print(f"  Overall Score: {summary['overall_score']:.1f}/5")

        # Generate and save report
        report = generator.render_session_report(session)

        if output:
            output_path = Path(output)
            output_path.write_text(report)
            console.print(f"\n[green]✓[/green] Report saved to: {output_path}")
        else:
            console.print("\n" + report)

    except ImportError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("  Install AI dependencies: pip install 'resume-cli[ai]'")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error in mock interview:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("job-parse")
@click.option(
    "--file", "file_input", type=click.Path(exists=True), help="Path to job posting HTML file"
)
@click.option("--url", type=str, help="URL to job posting")
@click.option("-o", "--output", type=click.Path(), help="Save parsed data as JSON")
@click.option("--no-cache", is_flag=True, help="Disable caching of parsed job postings")
def job_parse(file_input: Optional[str], url: Optional[str], output: Optional[str], no_cache: bool):
    """
    Parse job posting from LinkedIn, Indeed, or other sources.

    Extracts structured data (company, position, requirements, responsibilities,
    salary, remote status) for use with AI resume tailoring.

    Examples:
        resume-cli job-parse --url https://linkedin.com/jobs/view/12345
        resume-cli job-parse --file job-posting.html
        resume-cli job-parse --url URL --output job-data.json
    """
    console.print("[bold blue]Parsing Job Posting[/bold blue]")

    if not file_input and not url:
        console.print("[bold red]Error:[/bold red] Either --file or --url must be provided")
        console.print("  Use --file for local HTML files")
        console.print("  Use --url for web URLs")
        sys.exit(1)

    try:
        from .integrations.job_parser import JobParser

        cache_dir = None if no_cache else None
        parser = JobParser(cache_dir=cache_dir)

        if file_input:
            console.print(f"  File: {file_input}")
            job_details = parser.parse_from_file(Path(file_input), url=url)
        elif url:
            console.print(f"  URL: {url}")
            job_details = parser.parse_from_url(url)

        # Display results
        console.print("\n[bold green]Parsed Job Details:[/bold green]\n")
        console.print(f"  [cyan]Company:[/cyan] {job_details.company}")
        console.print(f"  [cyan]Position:[/cyan] {job_details.position}")

        if job_details.location:
            console.print(f"  [cyan]Location:[/cyan] {job_details.location}")

        if job_details.remote is not None:
            remote_text = "Yes" if job_details.remote else "No"
            console.print(f"  [cyan]Remote:[/cyan] {remote_text}")

        if job_details.salary:
            console.print(f"  [cyan]Salary:[/cyan] {job_details.salary}")

        if job_details.job_type:
            console.print(f"  [cyan]Job Type:[/cyan] {job_details.job_type}")

        if job_details.experience_level:
            console.print(f"  [cyan]Experience Level:[/cyan] {job_details.experience_level}")

        if job_details.requirements:
            console.print("\n  [cyan]Requirements:[/cyan]")
            for req in job_details.requirements[:5]:
                console.print(f"    - {req}")
            if len(job_details.requirements) > 5:
                console.print(f"    ... and {len(job_details.requirements) - 5} more")

        if job_details.responsibilities:
            console.print("\n  [cyan]Responsibilities:[/cyan]")
            for resp in job_details.responsibilities[:5]:
                console.print(f"    - {resp}")
            if len(job_details.responsibilities) > 5:
                console.print(f"    ... and {len(job_details.responsibilities) - 5} more")

        if job_details.benefits:
            console.print("\n  [cyan]Benefits:[/cyan]")
            for benefit in job_details.benefits[:3]:
                console.print(f"    - {benefit}")

        # Save to output file
        if output:
            output_path = Path(output)
            output_path.write_text(job_details.to_json())
            console.print(f"\n[green]✓[/green] Saved to: {output_path}")

    except NotImplementedError as e:
        console.print(f"[yellow]Note:[/yellow] {e}")
    except Exception as e:
        console.print(f"[bold red]Error parsing job posting:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("find-connections")
@click.option("--company", required=True, help="Target company name")
@click.option("--role", default="", help="Role/department to filter by")
@click.option("--no-linkedin", is_flag=True, help="Disable LinkedIn search")
@click.option("--no-github", is_flag=True, help="Disable GitHub search")
@click.option("--include-alumni", is_flag=True, help="Include alumni search")
@click.option("--include-previous", is_flag=True, help="Include previous company connections")
@click.option("--draft-message", is_flag=True, help="Generate outreach message suggestions")
@click.option("-o", "--output", type=click.Path(), help="Export connections to CSV file")
def find_connections(
    company: str,
    role: str,
    no_linkedin: bool,
    no_github: bool,
    include_alumni: bool,
    include_previous: bool,
    draft_message: bool,
    output: Optional[str],
):
    """
    Find professional connections at target companies.

    Helps users find alumni, former colleagues, and other connections
    at companies they're interested in for networking.

    Examples:
        resume-cli find-connections --company "Stripe"
        resume-cli find-connections --company "Google" --role "Engineering"
        resume-cli find-connections --company "Meta" --include-alumni --draft-message
    """
    from .integrations.connection_finder import ConnectionFinder

    console.print("[bold blue]Connection Finder[/bold blue]")
    console.print(f"  Company: {company}")
    if role:
        console.print(f"  Role: {role}")

    try:
        finder = ConnectionFinder()

        # Find connections
        connections = finder.find_connections(
            company=company,
            role=role,
            use_linkedin=not no_linkedin,
            use_github=not no_github,
        )

        # Find alumni if requested
        if include_alumni:
            alumni = finder.find_alumni(company)
            connections.extend(alumni)

        # Find previous company connections if requested
        if include_previous:
            prev_connections = finder.find_previous_company_connections(company)
            connections.extend(prev_connections)

        # Print connections table
        finder.print_connections_table(connections)

        # Generate outreach suggestions if requested
        if draft_message and connections:
            console.print("\n[bold]Outreach Message Suggestions[/bold]\n")
            suggestions = finder.generate_outreach_suggestions(connections)

            for i, suggestion in enumerate(suggestions[:3], 1):
                console.print(f"### {i}. {suggestion.connection.name}")
                console.print(f"   **Common Ground:** {suggestion.common_ground}")
                console.print("")
                console.print(suggestion.message_template)
                console.print("")
                console.print("**Talking Points:**")
                for point in suggestion.talking_points[:3]:
                    console.print(f"  - {point}")
                console.print("")

        # Export to CSV if requested
        if output and connections:
            output_path = Path(output)
            finder.export_to_csv(connections, output_path)

    except Exception as e:
        console.print(f"[bold red]Error finding connections:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("salary-research")
@click.option("--title", required=True, help="Job title")
@click.option("--location", default="", help="Job location")
@click.option("--company", default="", help="Company name")
@click.option(
    "--level",
    type=click.Choice(["entry", "mid", "senior", "staff", "principal"]),
    default="mid",
    help="Experience level",
)
@click.option("-o", "--output", type=click.Path(), help="Save report as JSON file")
def salary_research(title: str, location: str, company: str, level: str, output: Optional[str]):
    """
    Research salary data for a position.

    Provides estimated salary ranges based on job title, location, company,
    and experience level. Uses market data to generate estimates.

    Examples:
        resume-cli salary-research --title "Senior Backend Engineer" --location "San Francisco"
        resume-cli salary-research --title "Product Manager" --company "Google" --level senior
        resume-cli salary-research --title "ML Engineer" --location "New York" --company "Stripe" -o salary.json
    """
    from .integrations.salary_research import SalaryResearch

    console.print("[bold blue]Salary Research[/bold blue]")
    console.print(f"  Title: {title}")
    if location:
        console.print(f"  Location: {location}")
    if company:
        console.print(f"  Company: {company}")
    console.print(f"  Level: {level}")

    try:
        research = SalaryResearch()
        salary_data = research.research(
            title=title,
            location=location,
            company=company,
            experience_level=level,
        )

        # Print report
        research.print_salary_report(salary_data)

        # Export to JSON if requested
        if output:
            output_path = Path(output)
            research.export_json(salary_data, output_path)
            console.print(f"[green]✓[/green] Report saved to: {output_path}")

    except Exception as e:
        console.print(f"[bold red]Error researching salary:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Offer comparison commands
@cli.group()
def offer():
    """Offer comparison commands."""
    pass


@offer.command("add")
@click.option("--company", required=True, help="Company name")
@click.option("--role", required=True, help="Job role/title")
@click.option("--base", "base_salary", type=float, default=0, help="Annual base salary")
@click.option("--bonus", type=float, default=0, help="Annual bonus")
@click.option("--equity", type=float, default=0, help="Total equity value")
@click.option("--equity-years", type=int, default=4, help="Equity vesting years")
@click.option("--benefits", "benefits_value", type=float, default=0, help="Annual benefits value")
@click.option("--location", type=str, default="", help="Job location")
@click.option("--remote", is_flag=True, help="Is remote position")
@click.option("--notes", type=str, default="", help="Additional notes")
def offer_add(
    company: str,
    role: str,
    base_salary: float,
    bonus: float,
    equity: float,
    equity_years: int,
    benefits_value: float,
    location: str,
    remote: bool,
    notes: str,
):
    """
    Add a job offer for comparison.

    Examples:
        resume-cli offer add --company Stripe --role "Senior Engineer" --base 200000 --bonus 30000 --equity 320000
        resume-cli offer add --company Google --role "Staff Engineer" --base 220000 --remote
    """
    from .integrations.offer_comparison import add_offer as add_offer_func

    try:
        add_offer_func(
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
        console.print(f"[green]✓[/green] Added offer from {company}")

    except Exception as e:
        console.print(f"[bold red]Error adding offer:[/bold red] {e}")
        sys.exit(1)


@offer.command("compare")
@click.option("-o", "--output", type=click.Path(), help="Save report to file")
def offer_compare(output: Optional[str]):
    """
    Compare all stored offers and show weighted scores.

    Examples:
        resume-cli offer compare
        resume-cli offer compare -o comparison.md
    """
    from .integrations.offer_comparison import generate_report

    try:
        report = generate_report()

        if output:
            output_path = Path(output)
            output_path.write_text(report)
            console.print(f"[green]✓[/green] Report saved to: {output_path}")
        else:
            console.print(report)

    except Exception as e:
        console.print(f"[bold red]Error comparing offers:[/bold red] {e}")
        sys.exit(1)


@offer.command("list")
def offer_list():
    """List all stored offers."""
    from .integrations.offer_comparison import OfferComparison

    try:
        comparison = OfferComparison()
        offers = comparison.list_offers()

        if not offers:
            console.print("[yellow]No offers stored.[/yellow]")
            console.print("  Add offers using: resume-cli offer add")
            return

        table = Table(title="Stored Offers")
        table.add_column("Company", style="cyan")
        table.add_column("Role", style="white")
        table.add_column("Total Comp", style="green", justify="right")
        table.add_column("Location", style="yellow")

        for o in offers:
            table.add_row(o.company, o.role, f"${o.total_compensation:,.0f}", o.location or "N/A")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error listing offers:[/bold red] {e}")
        sys.exit(1)


@offer.command("priorities")
@click.option("--salary", type=int, default=30, help="Salary weight (0-100)")
@click.option("--growth", type=int, default=25, help="Career growth weight (0-100)")
@click.option("--wlb", type=int, default=25, help="Work-life balance weight (0-100)")
@click.option("--benefits", type=int, default=20, help="Benefits weight (0-100)")
def offer_priorities(salary: int, growth: int, wlb: int, benefits: int):
    """
    Set priorities for offer comparison.

    Examples:
        resume-cli offer priorities --salary 40 --growth 30 --wlb 20 --benefits 10
    """
    from .integrations.offer_comparison import set_priorities

    try:
        set_priorities(salary=salary, growth=growth, wlb=wlb, benefits=benefits)
        console.print("[green]✓[/green] Priorities updated:")
        console.print(f"  Salary: {salary}%")
        console.print(f"  Growth: {growth}%")
        console.print(f"  Work-Life Balance: {wlb}%")
        console.print(f"  Benefits: {benefits}%")

    except Exception as e:
        console.print(f"[bold red]Error setting priorities:[/bold red] {e}")
        sys.exit(1)


@offer.command("clear")
@click.confirmation_option(prompt="Are you sure you want to delete all stored offers?")
def offer_clear():
    """Clear all stored offers."""
    from .integrations.offer_comparison import OfferComparison

    try:
        comparison = OfferComparison()
        comparison.clear_offers()
        console.print("[green]✓[/green] All offers cleared")

    except Exception as e:
        console.print(f"[bold red]Error clearing offers:[/bold red] {e}")
        sys.exit(1)

        sys.exit(1)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
