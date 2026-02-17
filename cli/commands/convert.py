"""
CLI command for converting between resume formats.

This module provides the 'convert' command for bidirectional conversion
between resume-cli YAML format and JSON Resume format.
"""

import json
from pathlib import Path

import click

from ..utils.json_resume_converter import JSONResumeConverter, convert_yaml_to_json_resume


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--to-json",
    "direction",
    flag_value="to_json",
    help="Convert YAML to JSON Resume format",
)
@click.option(
    "--to-yaml",
    "direction",
    flag_value="to_yaml",
    help="Convert JSON Resume to YAML format",
)
@click.option(
    "--format",
    type=click.Choice(["json", "yaml"]),
    help="Output format (optional, inferred from extension if not specified)",
)
@click.option(
    "--no-variants",
    is_flag=True,
    default=False,
    help="Don't add default variants configuration when converting to YAML",
)
def convert(input_file: Path, output_file: Path, direction: str, format: str, no_variants: bool):
    """
    Convert resume data between different formats.
    
    Converts between:
    - resume-cli YAML format (resume.yaml)
    - JSON Resume format (https://jsonresume.org/schema/)
    
    INPUT_FILE: Path to input file
    OUTPUT_FILE: Path to output file
    
    Examples:
    
        # Convert YAML to JSON Resume:
        resume-cli convert resume.yaml resume.json --to-json
        
        # Convert JSON Resume to YAML:
        resume-cli convert resume.json my-resume.yaml --to-yaml
        
        # Auto-detect direction from file extensions:
        resume-cli convert resume.yaml resume.json
    """
    # Auto-detect direction if not specified
    if not direction:
        input_ext = input_file.suffix.lower()
        output_ext = output_file.suffix.lower()
        
        if input_ext in [".yaml", ".yml"] and output_ext == ".json":
            direction = "to_json"
        elif input_ext == ".json" and output_ext in [".yaml", ".yml"]:
            direction = "to_yaml"
        else:
            click.echo(
                "Error: Could not auto-detect conversion direction. "
                "Please specify --to-json or --to-yaml",
                err=True,
            )
            raise click.Abort()
    
    try:
        if direction == "to_json":
            # Convert YAML to JSON Resume
            click.echo(f"Converting {input_file} to JSON Resume format...")
            
            json_resume = convert_yaml_to_json_resume(input_file, output_file)
            
            click.echo(f"✓ Successfully converted to JSON Resume: {output_file}")
            
            # Show summary
            basics = json_resume.get("basics", {})
            click.echo(f"  Name: {basics.get('name', 'N/A')}")
            click.echo(f"  Email: {basics.get('email', 'N/A')}")
            
            work_count = len(json_resume.get("work", []))
            click.echo(f"  Work entries: {work_count}")
            
            edu_count = len(json_resume.get("education", []))
            click.echo(f"  Education entries: {edu_count}")
            
            skill_count = len(json_resume.get("skills", []))
            click.echo(f"  Skills categories: {skill_count}")
            
        elif direction == "to_yaml":
            # Convert JSON Resume to YAML
            click.echo(f"Converting {input_file} to resume-cli YAML format...")
            
            with open(input_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            
            yaml_data = JSONResumeConverter.json_resume_to_yaml(json_data, include_variants=not no_variants)
            
            # Save using yaml_parser
            from ..utils.yaml_parser import ResumeYAML
            
            yaml_handler = ResumeYAML(output_file)
            yaml_handler.save(yaml_data)
            
            click.echo(f"✓ Successfully converted to YAML: {output_file}")
            
            # Show summary
            contact = yaml_data.get("contact", {})
            click.echo(f"  Name: {contact.get('name', 'N/A')}")
            click.echo(f"  Email: {contact.get('email', 'N/A')}")
            
            exp_count = len(yaml_data.get("experience", []))
            click.echo(f"  Experience entries: {exp_count}")
            
            edu_count = len(yaml_data.get("education", []))
            click.echo(f"  Education entries: {edu_count}")
            
            skill_count = len(yaml_data.get("skills", {}))
            click.echo(f"  Skills categories: {skill_count}")
            
            if not no_variants:
                variant_count = len(yaml_data.get("variants", {}))
                click.echo(f"  Variants: {variant_count}")
        
    except Exception as e:
        click.echo(f"Error during conversion: {e}", err=True)
        raise click.Abort()


@click.command(name="import-json-resume")
@click.argument("json_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output YAML file path (default: resume.yaml)",
)
def import_json_resume(json_file: Path, output: Path):
    """
    Import a JSON Resume file to resume-cli YAML format.
    
    This is a convenience command that converts JSON Resume format
    to the resume-cli YAML format.
    
    JSON_FILE: Path to JSON Resume file
    
    Examples:
    
        resume-cli import-json-resume resume.json
        resume-cli import-json-resume resume.json -o my-resume.yaml
    """
    if output is None:
        output = Path("resume.yaml")
    
    click.echo(f"Importing JSON Resume from {json_file}...")
    
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    yaml_data = JSONResumeConverter.json_resume_to_yaml(json_data, include_variants=True)
    
    from ..utils.yaml_parser import ResumeYAML
    
    yaml_handler = ResumeYAML(output)
    yaml_handler.save(yaml_data)
    
    click.echo(f"✓ Successfully imported to: {output}")


@click.command(name="export-json-resume")
@click.argument("yaml_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output JSON file path (default: resume.json)",
)
def export_json_resume(yaml_file: Path, output: Path):
    """
    Export resume-cli YAML to JSON Resume format.
    
    This is a convenience command that converts resume-cli YAML format
    to JSON Resume format for use with other tools.
    
    YAML_FILE: Path to resume.yaml file
    
    Examples:
    
        resume-cli export-json-resume resume.yaml
        resume-cli export-json-resume resume.yaml -o resume.json
    """
    if output is None:
        output = Path("resume.json")
    
    click.echo(f"Exporting to JSON Resume format...")
    
    json_resume = convert_yaml_to_json_resume(yaml_file, output)
    
    click.echo(f"✓ Successfully exported to: {output}")
    click.echo(f"  You can now use this file with ResumeAI or other JSON Resume tools")
