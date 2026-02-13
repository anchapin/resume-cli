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
from .utils.schema import ResumeValidator
from .generators.template import TemplateGenerator

# Initialize rich console
console = Console()

# Default paths
DEFAULT_YAML_PATH = Path(__file__).parent.parent / "resume.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default.yaml"


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--yaml-path",
    type=click.Path(exists=True),
    default=str(DEFAULT_YAML_PATH),
    help="Path to resume.yaml file"
)
@click.option(
    "--config-path",
    type=click.Path(exists=True),
    default=str(DEFAULT_CONFIG_PATH),
    help="Path to config file"
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
@click.option(
    "--from-existing",
    is_flag=True,
    help="Initialize from existing resume files"
)
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
                output_path=job_hunt_dir / "resume.yaml"
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
@click.option(
    "-v", "--variant",
    default="v1.0.0-base",
    help="Resume variant to generate"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["md", "tex", "pdf"]),
    default="md",
    help="Output format"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (default: auto-generated)"
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Print to stdout without saving"
)
@click.option(
    "--ai",
    is_flag=True,
    help="Use AI-powered generation (requires API key)"
)
@click.option(
    "--job-desc",
    type=click.Path(exists=True),
    help="Path to job description file for AI customization"
)
@click.pass_context
def generate(ctx, variant: str, format: str, output: Optional[str], no_save: bool, ai: bool, job_desc: Optional[str]):
    """
    Generate resume from template or AI.

    Examples:
        resume-cli generate -v v1.0.0-base -f md
        resume-cli generate -v v1.1.0-backend -f pdf -o my-resume.pdf
        resume-cli generate --ai --job-desc job-posting.txt
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print(f"[bold blue]Generating resume: {variant}[/bold blue]")
    console.print(f"  Format: {format.upper()}")

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
                base_path = TemplateGenerator(yaml_path, config=config).get_output_path(variant, format)
                stem = base_path.stem
                output_path = base_path.parent / f"{stem}-ai{base_path.suffix}"

            content = generator.generate(
                variant=variant,
                job_description=job_description,
                output_format=format,
                output_path=output_path
            )
        else:
            generator = TemplateGenerator(yaml_path, config=config)

            if output_path is None and not no_save:
                output_path = generator.get_output_path(variant, format)

            content = generator.generate(
                variant=variant,
                output_format=format,
                output_path=output_path
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
@click.option(
    "-v", "--variant",
    default="v1.0.0-base",
    help="Resume variant to generate"
)
@click.option(
    "-f", "--format",
    type=click.Choice(["md", "tex", "pdf"]),
    default="md",
    help="Deprecated: generate-package always produces both MD and PDF formats"
)
@click.option(
    "--job-desc",
    type=click.Path(exists=True),
    required=True,
    help="Path to job description file"
)
@click.option(
    "--company",
    type=str,
    help="Company name (overrides extraction from job description)"
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Skip questions, use smart defaults"
)
@click.option(
    "--no-cover-letter",
    is_flag=True,
    help="Skip cover letter generation"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory (default: config setting)"
)
@click.option(
    "--include-github-projects",
    is_flag=True,
    help="Auto-select and include GitHub projects matching job technologies (searches repos AND code in organization)"
)
@click.pass_context
def generate_package(ctx, variant: str, format: str, job_desc: str, company: Optional[str],
                     non_interactive: bool, no_cover_letter: bool, output_dir: Optional[str],
                     include_github_projects: bool):
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
        company_slug = re.sub(r'[^\w\s-]', '', company_name).strip().lower()[:30]
        company_slug = re.sub(r'[-\s]+', '-', company_slug)
        package_dir = output_base_dir / f"{company_slug}-{date_str}"
        package_dir.mkdir(parents=True, exist_ok=True)

        # Step 1.5: Auto-select GitHub projects if requested
        enhanced_context = {}
        if include_github_projects:
            console.print("\n[cyan]Step 1.5: Selecting GitHub projects matching job technologies...[/cyan]")
            try:
                from .integrations.github_sync import GitHubSync

                # Extract technologies from job description using AI
                technologies = resume_gen.extract_technologies(job_description)

                if not technologies:
                    console.print("[yellow]Warning:[/yellow] No technologies extracted from job description.")
                    console.print("  Continuing without GitHub projects.")
                else:
                    console.print(f"[dim]Extracted technologies: {', '.join(technologies)}[/dim]")
                    console.print(f"[dim]Using top 3 for matching: {', '.join(technologies[:3])}[/dim]")
                    console.print("[dim]Searching for code in organization...[/dim]")

                    # Select matching projects
                    github_sync = GitHubSync(config)
                    max_projects = config.get("github.max_projects", 3)
                    months = config.get("github.sync_months", 12)

                    selected_projects = github_sync.select_matching_projects(
                        technologies=technologies,
                        top_n=max_projects,
                        months=months
                    )

                    if not selected_projects:
                        top_techs = technologies[:3]
                        console.print(f"[yellow]Warning:[/yellow] No matching GitHub projects found for: {', '.join(top_techs)}")
                        console.print("  Continuing without GitHub projects.")
                    else:
                        console.print(f"[green]✓[/green] Selected {len(selected_projects)} GitHub projects:")
                        for proj in selected_projects:
                            console.print(f"    • {proj['name']} ({proj['language']}) - score: {proj['match_score']}")

                        # Enhance project descriptions with AI (ephemeral - doesn't modify resume.yaml)
                        enhanced_projects = resume_gen.enhance_project_descriptions(
                            projects=selected_projects,
                            job_description=job_description,
                            technologies=technologies
                        )

                        # Generate enhanced professional summary integrating projects
                        base_summary = ctx.obj["yaml_handler"].get_summary(variant)
                        enhanced_summary = resume_gen.generate_project_summary(
                            enhanced_projects=enhanced_projects,
                            base_summary=base_summary,
                            variant=variant
                        )

                        # Build enhanced context for template rendering
                        enhanced_context = {
                            "projects": {"featured": enhanced_projects},
                            "summary": enhanced_summary,
                        }

                        console.print("[dim]AI enhancements applied (ephemeral - resume.yaml unchanged)[/dim]")

            except RuntimeError as e:
                console.print(f"[yellow]Warning:[/yellow] GitHub CLI error: {e}")
                console.print("  Continuing without GitHub projects. Make sure 'gh' CLI is installed and authenticated.")
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
                enhanced_context=enhanced_context if enhanced_context else None
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
                    output_formats=config.cover_letter_formats
                )
            else:
                cover_letter_outputs, job_details = cl_gen_temp.generate_interactive(
                    job_description=job_description,
                    company_name=company,
                    variant=variant,
                    output_formats=config.cover_letter_formats
                )

            # Save cover letter outputs
            cover_letter_paths = cl_gen_temp.save_outputs(
                outputs=cover_letter_outputs,
                company_name=company_name,
                output_dir=package_dir
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

            table.add_row(
                name,
                config.get("description", ""),
                summary,
                skills
            )

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
@click.option(
    "-r", "--role",
    help="Job role/title"
)
@click.option(
    "-v", "--variant",
    default="v1.0.0-base",
    help="Resume variant used"
)
@click.option(
    "-s", "--source",
    default="manual",
    help="Application source"
)
@click.option(
    "-u", "--url",
    help="Job posting URL"
)
@click.option(
    "-n", "--notes",
    help="Additional notes"
)
@click.pass_context
def apply(ctx, company: str, status: str, role: Optional[str], variant: str,
          source: str, url: Optional[str], notes: Optional[str]):
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
            notes=notes
        )

        console.print(f"[green]✓[/green] Logged application: {company}")

    except Exception as e:
        console.print(f"[bold red]Error logging application:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--months",
    type=int,
    default=3,
    help="Number of months to look back"
)
@click.pass_context
def sync_github(ctx, months: int):
    """Sync GitHub projects to resume.yaml."""
    from .integrations.github_sync import GitHubSync

    config = ctx.obj["config"]
    yaml_handler = ctx.obj["yaml_handler"]

    console.print(f"[bold blue]Syncing GitHub projects (past {months} months)...[/bold blue]")

    try:
        sync = GitHubSync(config)
        projects = sync.fetch_projects(months=months)

        console.print(f"[green]✓[/green] Found {len(projects.get('ai_ml', [])) + len(projects.get('fullstack', []))} projects")

        # TODO: Update resume.yaml with projects
        console.print("[yellow]Note:[/yellow] Auto-update of resume.yaml coming soon.")
        console.print("  Current projects fetched successfully.")

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


@cli.command("interview-prep")
@click.option(
    "-v", "--variant",
    default="v1.0.0-base",
    help="Resume variant to use for context"
)
@click.option(
    "--job-desc",
    type=click.Path(exists=True),
    required=True,
    help="Path to job description file"
)
@click.option(
    "--num-technical",
    type=int,
    default=10,
    help="Number of technical questions to generate (default: 10)"
)
@click.option(
    "--num-behavioral",
    type=int,
    default=5,
    help="Number of behavioral questions to generate (default: 5)"
)
@click.option(
    "--no-system-design",
    is_flag=True,
    help="Skip system design questions"
)
@click.option(
    "--flashcard-mode",
    is_flag=True,
    help="Generate flashcard format (optimized for studying)"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (default: auto-generated)"
)
@click.pass_context
def interview_prep(ctx, variant: str, job_desc: str, num_technical: int,
                  num_behavioral: int, no_system_design: bool,
                  flashcard_mode: bool, output: Optional[str]):
    """
    Generate interview questions based on job description and resume.

    Generates personalized technical and behavioral interview questions,
    complete with context, answers, and tips.

    Output includes:
    - Technical questions with domain-specific focus
    - Behavioral questions with STAR framework
    - System design questions (unless disabled)
    - Job analysis with key technologies and focus areas

    Examples:
        resume-cli interview-prep --job-desc job-posting.txt
        resume-cli interview-prep --job-desc job.txt --flashcard-mode -o interview-questions.md
        resume-cli interview-prep --job-desc job.txt --num-technical 15 --num-behavioral 8
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    console.print(f"[bold blue]Generating interview questions...[/bold blue]")
    console.print(f"  Variant: {variant}")
    console.print(f"  Technical Questions: {num_technical}")
    console.print(f"  Behavioral Questions: {num_behavioral}")
    console.print(f"  System Design: {'No' if no_system_design else 'Yes'}")
    console.print(f"  Flashcard Mode: {'Yes' if flashcard_mode else 'No'}")

    # Check if yaml exists
    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Read job description
    job_description = Path(job_desc).read_text()

    try:
        from .generators.interview_questions_generator import InterviewQuestionsGenerator

        generator = InterviewQuestionsGenerator(yaml_path, config=config)

        # Generate questions
        questions_data = generator.generate(
            job_description=job_description,
            variant=variant,
            num_technical=num_technical,
            num_behavioral=num_behavioral,
            include_system_design=not no_system_design,
            flashcard_mode=flashcard_mode
        )

        # Render to markdown
        if flashcard_mode:
            content = generator.render_to_flashcards(questions_data)
        else:
            content = generator.render_to_markdown(questions_data)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Auto-generate filename based on job desc
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            mode = "-flashcards" if flashcard_mode else ""
            output_dir = Path(config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"interview-questions-{variant}{mode}-{date_str}.md"

        # Save content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        console.print(f"\n[green]✓[/green] Interview questions saved: {output_path}")

        # Show summary
        job_analysis = questions_data.get("job_analysis", {})
        console.print(f"\n[cyan]Job Analysis:[/cyan]")
        console.print(f"  Role: {job_analysis.get('role_type', 'Unknown')}")
        console.print(f"  Difficulty: {job_analysis.get('difficulty_estimate', 'Unknown')}")
        console.print(f"  Technologies: {len(job_analysis.get('key_technologies', []))}")

        tech_questions = questions_data.get("technical_questions", [])
        behavioral_questions = questions_data.get("behavioral_questions", [])
        system_design_questions = questions_data.get("system_design_questions")

        console.print(f"\n[cyan]Questions Generated:[/cyan]")
        console.print(f"  Technical: {len(tech_questions)} ({sum(1 for q in tech_questions if q.get('priority') == 'high')} high priority)")
        console.print(f"  Behavioral: {len(behavioral_questions)} ({sum(1 for q in behavioral_questions if q.get('priority') == 'high')} high priority)")
        if system_design_questions:
            console.print(f"  System Design: {len(system_design_questions)}")

    except Exception as e:
        console.print(f"[bold red]Error generating interview questions:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
