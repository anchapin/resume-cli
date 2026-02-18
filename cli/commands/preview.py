"""
CLI command for previewing generated resumes in a web browser.

This module provides the 'preview' command that starts a local web server
to visualize generated resumes directly in the browser.
"""

import os
import tempfile
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Optional

import click
import yaml as yaml_module
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup


@click.command()
@click.option(
    "--yaml",
    "-y",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to resume.yaml file (default: resume.yaml in current directory)",
)
@click.option(
    "--variant",
    "-v",
    default="base",
    help="Resume variant to preview (default: base)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=8080,
    help="Port to run preview server on (default: 8080)",
)
@click.option(
    "--no-open",
    is_flag=True,
    default=False,
    help="Don't open browser automatically",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "markdown", "latex"]),
    default="html",
    help="Preview format (default: html)",
)
def preview(
    yaml: Optional[Path],
    variant: str,
    port: int,
    no_open: bool,
    format: str,
):
    """
    Start a local web server to preview generated resumes.

    This command starts a web server that displays the resume in a visual format,
    making it easy to review the resume before exporting to PDF or other formats.

    Examples:

        # Preview default resume.yaml
        resume-cli preview

        # Preview specific YAML file
        resume-cli preview --yaml my-resume.yaml

        # Preview with specific variant
        resume-cli preview --variant backend

        # Preview on custom port
        resume-cli preview --port 3000

        # Preview without opening browser
        resume-cli preview --no-open
    """
    # Find the resume YAML file
    if yaml is None:
        yaml = Path("resume.yaml")

    if not yaml.exists():
        click.echo(f"Error: Resume file not found: {yaml}", err=True)
        raise click.Abort()

    # Load resume data
    click.echo(f"Loading resume from {yaml}...")
    with open(yaml, "r", encoding="utf-8") as f:
        resume_data = yaml_module.safe_load(f)

    # Generate HTML preview
    click.echo(f"Generating {format} preview...")

    try:
        if format == "html":
            html_content = generate_html_preview(resume_data, variant)
        elif format == "markdown":
            html_content = generate_markdown_preview(resume_data, variant)
        elif format == "latex":
            html_content = generate_latex_preview(resume_data, variant)
    except Exception as e:
        click.echo(f"Error generating preview: {e}", err=True)
        raise click.Abort()

    # Start the preview server
    start_preview_server(html_content, port, no_open)


def generate_html_preview(resume_data: dict, variant: str) -> str:
    """Generate HTML preview from resume data."""
    from cli.generators.template import TemplateGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_md = temp_path / "preview.md"

        # Generate Markdown using TemplateGenerator (then convert to HTML)
        generator = TemplateGenerator(yaml_path=None)
        generator.generate(
            variant=variant,
            output_format="md",
            output_path=output_md,
            resume_data=resume_data,
        )

        md_content = output_md.read_text(encoding="utf-8")

        # Convert Markdown to HTML using markdown library
        try:
            import markdown

            html = markdown.markdown(
                md_content,
                extensions=["extra", "codehilite", "tables", "toc"],
            )
            return wrap_in_html_template(html, "Resume Preview")
        except ImportError:
            # Fallback: wrap raw markdown in pre tags
            return wrap_in_html_template(
                f'<pre style="white-space: pre-wrap;">{md_content}</pre>',
                "Resume Preview",
            )


def generate_markdown_preview(resume_data: dict, variant: str) -> str:
    """Generate Markdown preview from resume data."""
    from cli.generators.template import TemplateGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_md = temp_path / "preview.md"

        # Generate Markdown using TemplateGenerator
        generator = TemplateGenerator(yaml_path=None)
        generator.generate(
            variant=variant,
            output_format="md",
            output_path=output_md,
            resume_data=resume_data,
        )

        md_content = output_md.read_text(encoding="utf-8")

        # Convert Markdown to HTML for preview
        try:
            import markdown

            html = markdown.markdown(
                md_content,
                extensions=["extra", "codehilite", "tables"],
            )
            return wrap_in_html_template(html, "Markdown Preview")
        except ImportError:
            # Fallback: display raw markdown
            return wrap_in_html_template(
                f'<pre style="white-space: pre-wrap;">{md_content}</pre>',
                "Markdown Preview",
            )


def generate_latex_preview(resume_data: dict, variant: str) -> str:
    """Generate LaTeX preview from resume data."""
    from cli.generators.template import TemplateGenerator

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_tex = temp_path / "preview.tex"

        # Generate LaTeX using TemplateGenerator
        generator = TemplateGenerator(yaml_path=None)
        generator.generate(
            variant=variant,
            output_format="tex",
            output_path=output_tex,
            resume_data=resume_data,
        )

        tex_content = output_tex.read_text(encoding="utf-8")

        # Escape for HTML display
        escaped = tex_content.replace("&", "&").replace("<", "<").replace(">", ">")
        return wrap_in_html_template(
            f'<pre style="white-space: pre-wrap; font-size: 12px;">{escaped}</pre>',
            "LaTeX Preview",
        )


def wrap_in_html_template(content: str, title: str) -> str:
    """Wrap content in HTML template."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header {{
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .contact {{
            color: #666;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
        }}
        .job, .education {{
            margin-bottom: 15px;
        }}
        .job-title, .school {{
            font-weight: bold;
        }}
        .company, .degree {{
            color: #666;
            font-style: italic;
        }}
        .date {{
            color: #999;
            font-size: 12px;
        }}
        .skills {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .skill {{
            background: #e9ecef;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 13px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""


def start_preview_server(html_content: str, port: int, no_open: bool):
    """Start HTTP server to serve the preview."""
    from http.server import HTTPServer, SimpleHTTPRequestHandler

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write HTML to temp file
        preview_file = temp_path / "preview.html"
        preview_file.write_text(html_content, encoding="utf-8")

        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(temp_path)

        # Create custom handler
        class PreviewHandler(SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                super().end_headers()

        # Start server
        server_address = ("", port)
        httpd = HTTPServer(server_address, PreviewHandler)

        url = f"http://localhost:{port}/preview.html"

        click.echo(f"\n✓ Preview server running at: {url}")
        click.echo(f"  Press Ctrl+C to stop the server\n")

        # Open browser
        if not no_open:
            Timer(1, lambda: webbrowser.open(url)).start()
            click.echo("  Browser opened automatically")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\n\n✓ Preview server stopped")
        finally:
            os.chdir(original_dir)
