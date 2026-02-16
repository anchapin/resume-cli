"""LinkedIn import/export commands."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--url", type=str, help="LinkedIn profile URL (not supported - requires data file)")
@click.option(
    "--data-file", type=click.Path(exists=True), help="Path to LinkedIn exported JSON data file"
)
@click.option("--output", type=click.Path(), help="Output YAML file path (default: resume.yaml)")
@click.option(
    "--merge", is_flag=True, help="Merge with existing resume.yaml instead of overwriting"
)
@click.option("--dry-run", is_flag=True, help="Preview changes without writing to file")
@click.pass_context
def linkedin_import(
    ctx,
    url: Optional[str],
    data_file: Optional[str],
    output: Optional[str],
    merge: bool,
    dry_run: bool,
):
    """
    Import LinkedIn profile data into resume.yaml.

    Due to LinkedIn API restrictions, you must export your LinkedIn data first:
    1. Go to https://www.linkedin.com/psettings/member-data
    2. Request 'Profile' data export
    3. Use the downloaded JSON file with --data-file

    Examples:
        # Import from exported JSON (creates new resume.yaml)
        resume-cli linkedin-import --data-file linkedin_data.json

        # Merge with existing resume.yaml
        resume-cli linkedin-import --data-file linkedin_data.json --merge

        # Preview changes before importing
        resume-cli linkedin-import --data-file linkedin_data.json --dry-run

        # Import to custom path
        resume-cli linkedin-import --data-file linkedin_data.json --output my-resume.yaml
    """
    import yaml

    from ..integrations.linkedin import LinkedInSync
    from ..utils.yaml_parser import ResumeYAML

    config = ctx.obj["config"]
    yaml_path = ctx.obj["yaml_path"]

    # Validate inputs
    if url and not data_file:
        console.print("[bold red]Error:[/bold red] Direct URL import is not supported.")
        console.print("\nPlease use --data-file option with exported LinkedIn JSON data.")
        console.print("\nTo export your LinkedIn data:")
        console.print("  1. Go to https://www.linkedin.com/psettings/member-data")
        console.print("  2. Request 'Profile' data export")
        console.print("  3. Use the downloaded JSON file")
        sys.exit(1)

    if not data_file:
        console.print("[bold red]Error:[/bold red] --data-file is required")
        sys.exit(1)

    data_file_path = Path(data_file)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = yaml_path

    console.print("[bold blue]Importing LinkedIn profile data...[/bold blue]")
    console.print(f"  Source: {data_file_path}")
    console.print(f"  Target: {output_path}")
    console.print(f"  Mode: {'Merge' if merge else 'Overwrite'}")

    try:
        # Import LinkedIn data
        sync = LinkedInSync(config)
        imported_data = sync.import_from_json(data_file_path)

        # Show summary of imported data
        console.print("\n[cyan]Imported data summary:[/cyan]")
        _print_import_summary(imported_data)

        # Handle merge or overwrite
        if merge and output_path.exists():
            console.print("\n[yellow]Merging with existing resume.yaml...[/yellow]")

            existing_data = ResumeYAML(output_path).load()
            merged_data = _merge_resume_data(existing_data, imported_data)

            if dry_run:
                console.print("\n[bold yellow]DRY RUN - No changes written[/bold yellow]")
                console.print(f"\nWould write to: {output_path}")
                _print_merge_summary(existing_data, merged_data)
            else:
                # Save merged data
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        merged_data,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
                console.print(f"[green]✓[/green] Merged data saved to {output_path}")
        else:
            if dry_run:
                console.print("\n[bold yellow]DRY RUN - No changes written[/bold yellow]")
                console.print(f"\nWould write to: {output_path}")
            else:
                # Save imported data (overwrite or new file)
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        imported_data,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
                console.print(f"[green]✓[/green] Imported data saved to {output_path}")

        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Review and edit resume.yaml as needed")
        console.print("  2. Run 'resume-cli validate' to check for errors")
        console.print("  3. Generate your resume: 'resume-cli generate'")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error importing data:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


@click.command()
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant to export")
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: output/linkedin-update.txt)",
)
@click.option(
    "--format", type=click.Choice(["linkedin", "plain"]), default="linkedin", help="Output format"
)
@click.pass_context
def linkedin_export(ctx, variant: str, output: Optional[str], format: str):
    """
    Export resume.yaml data to LinkedIn-friendly format.

    Exports your resume in a format suitable for updating your LinkedIn profile,
    including headline, experience, skills, education, and certifications.

    Examples:
        # Export for LinkedIn update
        resume-cli linkedin-export

        # Export specific variant
        resume-cli linkedin-export -v v1.1.0-backend

        # Export to custom file
        resume-cli linkedin-export -o my-linkedin-update.txt

        # Export plain text format
        resume-cli linkedin-export --format plain
    """
    config = ctx.obj["config"]
    yaml_path = ctx.obj["yaml_path"]

    if not yaml_path.exists():
        console.print(f"[bold red]Error:[/bold red] resume.yaml not found at {yaml_path}")
        console.print("  Run 'resume-cli init' to create it first.")
        sys.exit(1)

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_dir = config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "linkedin-update.txt"

    console.print("[bold blue]Exporting resume for LinkedIn...[/bold blue]")
    console.print(f"  Variant: {variant}")
    console.print(f"  Output: {output_path}")

    try:
        from ..integrations.linkedin import LinkedInSync

        sync = LinkedInSync(config)

        if format == "linkedin":
            sync.export_to_linkedin_format(yaml_path, output_path)
        else:
            # Plain text export - just dump YAML
            import yaml

            from ..utils.yaml_parser import ResumeYAML

            yaml_handler = ResumeYAML(yaml_path)
            data = yaml_handler.load()

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        console.print("\n[green]✓[/green] Export complete!")
        console.print(f"  File: {output_path}")

        # Show file size
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            console.print(f"  Size: {size_kb:.1f} KB")

        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Review the exported file")
        console.print("  2. Copy relevant sections to your LinkedIn profile")
        if format == "linkedin":
            console.print("  3. Note: LinkedIn has character limits for each field")
            console.print("  4. You may need to trim bullets to fit LinkedIn's format")

    except Exception as e:
        console.print(f"[bold red]Error exporting data:[/bold red] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _print_import_summary(data: dict) -> None:
    """Print summary of imported LinkedIn data."""
    contact = data.get("contact", {})
    console.print(f"  Name: {contact.get('name', 'N/A')}")
    console.print(f"  Email: {contact.get('email', 'N/A')}")

    summary = data.get("professional_summary", {}).get("base", "")
    if summary:
        console.print(f"  Summary: {summary[:80]}{'...' if len(summary) > 80 else ''}")

    skills = data.get("skills", {})
    total_skills = sum(len(v) for v in skills.values())
    console.print(f"  Skills: {total_skills} items in {len(skills)} categories")

    experience = data.get("experience", [])
    console.print(f"  Experience: {len(experience)} positions")

    education = data.get("education", [])
    console.print(f"  Education: {len(education)} entries")

    certifications = data.get("certifications", [])
    if certifications:
        console.print(f"  Certifications: {len(certifications)} items")


def _merge_resume_data(existing: dict, imported: dict) -> dict:
    """
    Merge imported LinkedIn data with existing resume data.

    Strategy:
    - Contact: Use imported (LinkedIn is authoritative)
    - Professional Summary: Keep existing, use imported as variant
    - Skills: Merge and deduplicate
    - Experience: Merge (LinkedIn may have more detail)
    - Education: Merge and deduplicate
    - Certifications: Merge and deduplicate
    - Projects: Keep existing (LinkedIn doesn't have project data)
    - Variants: Keep existing

    Args:
        existing: Existing resume data
        imported: Imported LinkedIn data

    Returns:
        Merged data dictionary
    """
    merged = existing.copy()

    # Contact: Use imported data
    merged["contact"] = imported.get("contact", existing.get("contact", {}))

    # Professional Summary: Keep existing base, add imported as variant
    if imported.get("professional_summary"):
        if "variants" not in merged["professional_summary"]:
            merged["professional_summary"]["variants"] = {}
        imported_summary = imported["professional_summary"].get("base", "")
        if imported_summary:
            merged["professional_summary"]["variants"]["linkedin_import"] = imported_summary

    # Skills: Merge and deduplicate
    imported_skills = imported.get("skills", {})
    existing_skills = existing.get("skills", {})

    # Handle case where imported_skills might not be a dict (e.g., from malformed data)
    if not isinstance(imported_skills, dict):
        imported_skills = {}
    if not isinstance(existing_skills, dict):
        existing_skills = {}

    for category, skill_list in imported_skills.items():
        if category not in existing_skills:
            existing_skills[category] = []
        elif not isinstance(existing_skills[category], list):
            existing_skills[category] = []

        # Deduplicate and merge
        existing_skills_set = set()
        if isinstance(existing_skills[category], list):
            for skill in existing_skills[category]:
                if isinstance(skill, str):
                    existing_skills_set.add(skill.lower())
                elif isinstance(skill, dict):
                    existing_skills_set.add(skill.get("name", "").lower())

        for skill in skill_list:
            if isinstance(skill, str):
                if skill.lower() not in existing_skills_set:
                    existing_skills[category].append(skill)
                    existing_skills_set.add(skill.lower())
            elif isinstance(skill, dict):
                skill_name = skill.get("name", "")
                if skill_name.lower() not in existing_skills_set:
                    existing_skills[category].append(skill)
                    existing_skills_set.add(skill_name.lower())

    merged["skills"] = existing_skills

    # Experience: Merge (LinkedIn may have more positions)
    imported_exp = imported.get("experience", [])
    existing_exp = existing.get("experience", [])

    # Deduplicate by company + title + start_date
    existing_exp_keys = set()
    for exp in existing_exp:
        key = f"{exp.get('company', '')}|{exp.get('title', '')}|{exp.get('start_date', '')}"
        existing_exp_keys.add(key.lower())

    for exp in imported_exp:
        key = f"{exp.get('company', '')}|{exp.get('title', '')}|{exp.get('start_date', '')}"
        if key.lower() not in existing_exp_keys:
            existing_exp.append(exp)

    # Sort by start date
    existing_exp.sort(
        key=lambda x: (x.get("start_date", "") or "1900-01", x.get("end_date", "") or "9999-12"),
        reverse=True,
    )

    merged["experience"] = existing_exp

    # Education: Merge and deduplicate
    imported_edu = imported.get("education", [])
    existing_edu = existing.get("education", [])

    existing_edu_keys = set()
    for edu in existing_edu:
        key = f"{edu.get('institution', '')}|{edu.get('degree', '')}"
        existing_edu_keys.add(key.lower())

    for edu in imported_edu:
        key = f"{edu.get('institution', '')}|{edu.get('degree', '')}"
        if key.lower() not in existing_edu_keys:
            existing_edu.append(edu)

    merged["education"] = existing_edu

    # Certifications: Merge and deduplicate
    imported_certs = imported.get("certifications", [])
    existing_certs = existing.get("certifications", [])

    existing_certs_keys = set()
    for cert in existing_certs:
        key = f"{cert.get('name', '')}|{cert.get('issuer', '')}"
        existing_certs_keys.add(key.lower())

    for cert in imported_certs:
        key = f"{cert.get('name', '')}|{cert.get('issuer', '')}"
        if key.lower() not in existing_certs_keys:
            existing_certs.append(cert)

    merged["certifications"] = existing_certs

    # Update meta
    if "meta" in merged:
        merged["meta"]["last_updated"] = imported.get("meta", {}).get(
            "last_updated", merged["meta"].get("last_updated")
        )
        merged["meta"]["source"] = "linkedin_import"

    return merged


def _print_merge_summary(existing: dict, merged: dict) -> None:
    """Print summary of merge changes."""
    console.print("\n[cyan]Merge changes:[/cyan]")

    # Skills
    existing_skills = existing.get("skills", {})
    merged_skills = merged.get("skills", {})

    for category in set(list(existing_skills.keys()) + list(merged_skills.keys())):
        old_count = (
            len(existing_skills.get(category, []))
            if isinstance(existing_skills.get(category), list)
            else 0
        )
        new_count = (
            len(merged_skills.get(category, []))
            if isinstance(merged_skills.get(category), list)
            else 0
        )
        if new_count > old_count:
            console.print(
                f"  Skills.{category}: {old_count} → {new_count} (+{new_count - old_count})"
            )

    # Experience
    old_exp = len(existing.get("experience", []))
    new_exp = len(merged.get("experience", []))
    if new_exp > old_exp:
        console.print(f"  Experience: {old_exp} → {new_exp} (+{new_exp - old_exp})")

    # Education
    old_edu = len(existing.get("education", []))
    new_edu = len(merged.get("education", []))
    if new_edu > old_edu:
        console.print(f"  Education: {old_edu} → {new_edu} (+{new_edu - old_edu})")

    # Certifications
    old_certs = len(existing.get("certifications", []))
    new_certs = len(merged.get("certifications", []))
    if new_certs > old_certs:
        console.print(f"  Certifications: {old_certs} → {new_certs} (+{new_certs - old_certs})")
