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
    "-f", "--format", type=click.Choice(["md", "tex", "pdf", "txt", "docx"]), default="md", help="Output format"
)
@click.option(
    "-t", "--template",
    type=click.Choice(["base", "modern", "minimalist", "academic", "tech"]),
    default="base",
    help="Resume template style"
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
@click.pass_context
def generate(
    ctx,
    variant: str,
    format: str,
    template: str,
    output: Optional[str],
    no_save: bool,
    ai: bool,
    job_desc: Optional[str],
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

    console.print(f"[bold blue]Generating resume: {variant}[/bold blue]")
    console.print(f"  Format: {format.upper()}")
    console.print(f"  Template: {template}")

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

        # Generate
        if ai or job_description:
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
            )
        else:
            generator = TemplateGenerator(yaml_path, config=config)

            if output_path is None and not no_save:
                output_path = generator.get_output_path(variant, format)

            # Handle template selection (for non-AI generation)
            if template != "base":
                content = generator.generate(
                    variant=variant, 
                    output_format=format, 
                    output_path=output_path,
                    template=template
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

    console.print(f"[bold blue]Generating Application Package[/bold blue]")

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
        console.print(f"\n[bold green]Application package complete![/bold green]")
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

        console.print(f"[green]✓[/green] Updated resume.yaml with {new_projects_added} new projects")

        if backup_path:
            console.print(f"[dim]Backup saved to: {backup_path}[/dim]")
        
        console.print("\n[bold green]Done![/bold green] Run 'resume-cli variants' to see updated projects.")

    except Exception as e:
        console.print(f"[bold red]Error syncing GitHub:[/bold red] {e}")
        console.print("  Make sure 'gh' CLI is installed and authenticated.")
        sys.exit(1)


@cli.command()
@click.pass_context
def analyze(ctx):
    """Show application tracking analytics."""
    from .integrations.tracking import TrackingIntegration

    config = ctx.obj["config"]

    if not config.tracking_enabled:
        console.print("[yellow]Tracking is disabled in config.[/yellow]")
        sys.exit(0)

    try:
        tracker = TrackingIntegration(config)
        stats = tracker.get_statistics()

        console.print("\n[bold blue]Application Statistics[/bold blue]\n")

        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Applications", str(stats.get("total", 0)))
        table.add_row("Applied", str(stats.get("applied", 0)))
        table.add_row("Interviews", str(stats.get("interview", 0)))
        table.add_row("Offers", str(stats.get("offer", 0)))
        table.add_row("Response Rate", f"{stats.get('response_rate', 0):.1f}%")

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]No tracking data found.[/yellow]")
        console.print("  Start tracking with: resume-cli apply <company> <status>")
    except Exception as e:
        console.print(f"[bold red]Error analyzing:[/bold red] {e}")
        sys.exit(1)


# Add LinkedIn commands
from .commands.linkedin import linkedin_import, linkedin_export

cli.add_command(linkedin_import)
cli.add_command(linkedin_export)


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

    console.print(f"[bold blue]Checking ATS Compatibility[/bold blue]")
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

    console.print(f"[bold blue]Keyword Density Analysis[/bold blue]")
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
        from .generators.keyword_density import KeywordDensityGenerator

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


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
