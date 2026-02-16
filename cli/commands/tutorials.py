#!/usr/bin/env python3
"""
Interactive tutorials for Resume CLI commands.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()

# Tutorial content definitions
TUTORIALS = {
    "init": {
        "title": "First Time Setup",
        "description": "Learn how to initialize your resume.yaml",
        "steps": [
            {
                "title": "Understanding resume.yaml",
                "content": """resume.yaml is the single source of truth for your resume data.

All your resume variants are generated from this single file, keeping your data organized and easy to maintain.""",
            },
            {
                "title": "Running initialization",
                "content": """Run the init command to create your resume.yaml:

    resume-cli init --from-existing

This will parse your existing resume files and create a structured YAML file.""",
            },
            {
                "title": "Validating your data",
                "content": """After initialization, validate your resume.yaml:

    resume-cli validate

This checks for required fields, proper formatting, and data consistency.""",
            },
        ],
    },
    "generate": {
        "title": "Generate Your First Resume",
        "description": "Learn how to generate resumes from templates",
        "steps": [
            {
                "title": "Basic generation",
                "content": """Generate a simple Markdown resume:

    resume-cli generate -v v1.0.0-base -f md

This creates a resume using the base variant in Markdown format.""",
            },
            {
                "title": "Using variants",
                "content": """Variants let you customize your resume for different job types:

    resume-cli variants

Lists all available variants. Try:
    resume-cli generate -v v1.1.0-backend -f md""",
            },
            {
                "title": "PDF generation",
                "content": """Generate a PDF resume:

    resume-cli generate -v v1.0.0-base -f pdf

Note: Requires LaTeX to be installed on your system.""",
            },
        ],
    },
    "variants": {
        "title": "Using Variants",
        "description": "Understand and use resume variants",
        "steps": [
            {
                "title": "What are variants?",
                "content": """Variants are different versions of your resume tailored for specific job types.

For example:
- v1.0.0-base: General purpose
- v1.1.0-backend: Backend engineering
- v1.2.0-ml_ai: Machine learning/AI roles""",
            },
            {
                "title": "Listing variants",
                "content": """See all available variants:

    resume-cli variants

This shows each variant's description, summary, and skills.""",
            },
            {
                "title": "Creating variants",
                "content": """To create a new variant:
1. Add a new entry to variants: in resume.yaml
2. Define which skills and experience to emphasize
3. Use the variant with: resume-cli generate -v YOUR-VARIANT""",
            },
        ],
    },
    "ai": {
        "title": "AI-Powered Generation",
        "description": "Customize your resume with AI",
        "steps": [
            {
                "title": "Setting up AI",
                "content": """First, set up your AI API key:

    cp .env.template .env
    # Edit .env and add your ANTHROPIC_API_KEY

Or export directly:
    export ANTHROPIC_API_KEY=your_key_here""",
            },
            {
                "title": "Generating with AI",
                "content": """Generate an AI-customized resume:

    resume-cli generate --ai --job-desc job-posting.txt -v v1.1.0-backend

AI will:
- Extract keywords from the job description
- Reorder bullets to emphasize relevant experience
- Highlight matching skills""",
            },
            {
                "title": "Generate package",
                "content": """Create a complete application package:

    resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend

This generates both resume and cover letter, tailored to the job.""",
            },
        ],
    },
    "package": {
        "title": "Generate Application Package",
        "description": "Create complete job application materials",
        "steps": [
            {
                "title": "What is a package?",
                "content": """A package includes:
- AI-customized resume (MD + PDF)
- Tailored cover letter (MD + PDF)

All files are organized in a single directory.""",
            },
            {
                "title": "Basic package generation",
                "content": """Generate a package:

    resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend

Output goes to: output/{company}-{date}/""",
            },
            {
                "title": "Non-interactive mode",
                "content": """Skip the interactive prompts:

    resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive

AI will make smart guesses for the cover letter.""",
            },
        ],
    },
    "track": {
        "title": "Track Applications",
        "description": "Keep track of your job applications",
        "steps": [
            {
                "title": "Logging an application",
                "content": """Log a new application:

    resume-cli apply AcmeCorp applied -r "Senior Engineer"

Status options: applied, interview, offer, rejected, withdrawn""",
            },
            {
                "title": "Viewing statistics",
                "content": """See your application analytics:

    resume-cli analyze

Shows total applications, response rate, interview rate, etc.""",
            },
        ],
    },
    "github": {
        "title": "Sync GitHub Projects",
        "description": "Add your GitHub projects to your resume",
        "steps": [
            {
                "title": "Prerequisites",
                "content": """Ensure GitHub CLI is installed and authenticated:

    gh auth login

This allows resume-cli to access your repositories.""",
            },
            {
                "title": "Syncing projects",
                "content": """Fetch and preview GitHub projects:

    resume-cli sync-github --months 3

Shows projects from the last 3 months.""",
            },
            {
                "title": "Updating resume",
                "content": """To add projects to resume.yaml:

    resume-cli sync-github --months 3 --write

Creates a backup first. Use --no-backup to skip.""",
            },
        ],
    },
}


def list_tutorials():
    """List all available tutorials."""
    console.print("\n[bold cyan]Available Tutorials[/bold cyan]\n")

    for key, tutorial in TUTORIALS.items():
        console.print(f"  [cyan]{key:12}[/cyan] - {tutorial['title']}")
        console.print(f"               {tutorial['description']}")
        console.print()


def run_tutorial(tutorial_key: str):
    """Run an interactive tutorial."""
    if tutorial_key not in TUTORIALS:
        console.print(f"[red]Tutorial '{tutorial_key}' not found.[/red]")
        console.print("\nAvailable tutorials:")
        list_tutorials()
        return

    tutorial = TUTORIALS[tutorial_key]

    console.print(
        Panel(
            f"[bold cyan]{tutorial['title']}[/bold cyan]\n\n{tutorial['description']}",
            title="Tutorial",
        )
    )
    console.print()

    for i, step in enumerate(tutorial["steps"], 1):
        console.print(f"\n[bold yellow]Step {i}: {step['title']}[/bold yellow]\n")

        md = Markdown(step["content"])
        console.print(md)

        if i < len(tutorial["steps"]):
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

    console.print("\n[bold green]Tutorial complete![/bold green]")


@click.group()
def tutorial():
    """Interactive tutorials for Resume CLI commands."""
    pass


@tutorial.command("list")
def tutorial_list():
    """List all available tutorials."""
    list_tutorials()


@tutorial.command("run")
@click.argument("tutorial_name")
def tutorial_run(tutorial_name: str):
    """Run a specific tutorial."""
    run_tutorial(tutorial_name)


# Default run (no subcommand) shows list
@tutorial.command()
@click.argument("tutorial_name", required=False)
def main(tutorial_name: str):
    """Run or list tutorials."""
    if tutorial_name:
        run_tutorial(tutorial_name)
    else:
        list_tutorials()


if __name__ == "__main__":
    tutorial()
