"""Template-based resume generator."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.config import Config
from ..utils.template_utils import get_jinja_env, get_jinja_tex_env
from ..utils.yaml_parser import ResumeYAML

# Optional: resume_pdf_lib for enhanced PDF generation
try:
    from resume_pdf_lib import PDFGenerator as ResumePDFLibGenerator

    RESUME_PDF_LIB_AVAILABLE = True
except ImportError:
    RESUME_PDF_LIB_AVAILABLE = False


class TemplateGenerator:
    """Generate resumes from Jinja2 templates."""

    def __init__(
        self,
        yaml_path: Optional[Path] = None,
        template_dir: Optional[Path] = None,
        config: Optional[Config] = None,
        resume_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize template generator.

        Args:
            yaml_path: Path to resume.yaml
            template_dir: Path to templates directory
            config: Configuration object
            resume_data: Optional dictionary containing resume data
        """
        self.yaml_handler = ResumeYAML(yaml_path, resume_data=resume_data)
        self.config = config or Config()

        # Set up template directory
        if template_dir is None:
            # Default to templates/ in parent directory
            template_dir = Path(__file__).parent.parent.parent / "templates"

        self.template_dir = Path(template_dir)

        # Set up Jinja2 environment (cached via template_utils)
        self.env = get_jinja_env(self.template_dir)

        # Set up Jinja2 environment for LaTeX (cached via template_utils)
        # Separate environment for LaTeX with automatic escaping to prevent injection
        self.tex_env = get_jinja_tex_env(self.template_dir)

    def generate(
        self,
        variant: str,
        output_format: str = "md",
        output_path: Optional[Path] = None,
        enhanced_context: Optional[Dict[str, Any]] = None,
        template: str = "base",
        custom_template_path: Optional[Path] = None,
        **kwargs,
    ) -> str:
        """
        Generate resume from template.

        Args:
            variant: Variant name (e.g., "v1.0.0-base")
            output_format: Output format (md, tex, pdf)
            output_path: Optional output file path
            enhanced_context: Optional dict with AI-enhanced data to merge into context
                            (e.g., {"projects": {...}, "summary": "...", "skills": {...}})
            template: Template style (base, modern, minimalist, academic, tech)
            custom_template_path: Optional path to custom Jinja2 template file
                            (overrides template parameter)
            **kwargs: Additional template variables

        Returns:
            Generated content as string
        """
        # Load resume data
        variant_key = variant.replace("v1.", "").replace("v2.", "").split("-")[0]
        if variant_key.endswith(".0"):
            variant_key = variant_key.split(".")[0] + "." + variant_key.split(".")[1] + ".0"

        # Get variant config to determine summary key
        variant_config = self.yaml_handler.get_variant(variant)
        if not variant_config:
            # Try to extract the variant key from version
            if "backend" in variant:
                summary_key = "backend"
            elif "ml" in variant or "ai" in variant:
                summary_key = "ml_ai"
            elif "fullstack" in variant or "full" in variant:
                summary_key = "fullstack"
            elif "devops" in variant:
                summary_key = "devops"
            elif "leadership" in variant:
                summary_key = "leadership"
            else:
                summary_key = "base"
        else:
            summary_key = variant_config.get("summary_key", "base")

        # Extract technologies from enhanced_context for skills prioritization
        prioritize_technologies = None
        if enhanced_context:
            # Extract technologies from enhanced projects if available
            enhanced_projects = enhanced_context.get("projects", {}).get("featured", [])
            if enhanced_projects:
                all_techs = set()
                for proj in enhanced_projects:
                    if proj.get("highlighted_technologies"):
                        all_techs.update(proj["highlighted_technologies"])
                if all_techs:
                    prioritize_technologies = list(all_techs)

        # Prepare template context
        contact = self.yaml_handler.get_contact()
        # Ensure contact.location exists with default values for templates that expect it
        if "location" not in contact:
            contact["location"] = {"city": "", "state": "", "zip": ""}
        if "urls" not in contact:
            contact["urls"] = {"city": "", "state": "", "zip": ""}

        context = {
            "contact": contact,
            "summary": self.yaml_handler.get_summary(summary_key),
            "skills": self.yaml_handler.get_skills(
                variant, prioritize_technologies=prioritize_technologies
            ),
            "experience": self.yaml_handler.get_experience(variant),
            "education": self.yaml_handler.get_education(variant),
            "publications": self.yaml_handler.data.get("publications", []),
            "certifications": self.yaml_handler.data.get("certifications", []),
            "affiliations": self.yaml_handler.data.get("affiliations", []),
            "projects": self.yaml_handler.get_projects(variant),
            "variant": variant,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            **kwargs,
        }

        # Merge enhanced_context if provided (AI enhancements override base data)
        if enhanced_context:
            # Deep merge to preserve nested structure
            for key, value in enhanced_context.items():
                if key in context and isinstance(context[key], dict) and isinstance(value, dict):
                    # Merge dicts (e.g., projects, skills)
                    context[key].update(value)
                else:
                    # Replace non-dict values (e.g., summary)
                    context[key] = value

        # Select template (PDF uses TEX template, other formats use the selected style)
        template_format = "tex" if output_format == "pdf" else output_format

        # Select environment based on format
        # Use specialized LaTeX environment for tex/pdf to ensure security
        env = self.tex_env if template_format == "tex" else self.env

        # Handle custom template path
        if custom_template_path:
            try:
                # Load custom template from file path
                custom_template = Path(custom_template_path)
                if not custom_template.exists():
                    raise ValueError(f"Custom template not found: {custom_template_path}")

                # Read custom template content
                template_content = custom_template.read_text(encoding="utf-8")

                # Create a temporary template from string using the correct environment
                # This ensures filters and finalize hooks are available
                template = env.from_string(template_content)

            except Exception as e:
                if "Custom template not found" in str(e):
                    raise
                raise ValueError(f"Failed to load custom template: {e}")
        else:
            # Use built-in templates
            # For MD format, use template-specific template; otherwise use base
            if output_format == "md" and template != "base":
                template_name = f"resume_{template}_{template_format}.j2"
            else:
                template_name = f"resume_{template_format}.j2"

            try:
                template = env.get_template(template_name)
            except Exception:
                raise ValueError(f"Template not found: {template_name}")

        # Render
        content = template.render(**context)

        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # If PDF requested, compile from TEX (don't write LaTeX to PDF path)
            if output_format == "pdf" or output_path.suffix == ".pdf":
                self._compile_pdf(output_path, content)
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)

        return content

    def _compile_pdf(self, output_path: Path, tex_content: str) -> None:
        """
        Compile LaTeX to PDF.

        Args:
            output_path: Output PDF path
            tex_content: LaTeX content
        """
        # Create temporary .tex file
        tex_path = output_path.with_suffix(".tex")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Try pdflatex first
        pdf_created = False
        try:
            # Use Popen with explicit cleanup to avoid double-free issues
            process = subprocess.Popen(
                ["pdflatex", "-interaction=nonstopmode", "-no-shell-escape", tex_path.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tex_path.parent,
            )
            try:
                stdout, stderr = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise RuntimeError("PDF compilation timed out")

            if process.returncode == 0 or output_path.exists():
                pdf_created = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Check if PDF was created anyway (pdflatex returns non-zero for warnings)
            if output_path.exists():
                pdf_created = True
            else:
                # Fallback to pandoc
                try:
                    process = subprocess.Popen(
                        [
                            "pandoc",
                            str(tex_path),
                            "-o",
                            str(output_path),
                            "--pdf-engine=xelatex",
                            "--pdf-engine-opt=-no-shell-escape",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    try:
                        stdout, stderr = process.communicate(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout, stderr = process.communicate()
                        raise RuntimeError("PDF compilation timed out")

                    if process.returncode == 0 or output_path.exists():
                        pdf_created = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

        if not pdf_created or not output_path.exists():
            raise RuntimeError(
                "PDF compilation failed. Please install pdflatex or pandoc.\n"
                "  Ubuntu/Debian: sudo apt-get install texlive-full\n"
                "  macOS: brew install mactex\n"
                "  Or export as Markdown instead."
            )

    def generate_email(
        self,
        company_name: str,
        position_name: str,
        hiring_manager_name: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate cover letter/email.

        Args:
            company_name: Name of company
            position_name: Name of position
            hiring_manager_name: Optional hiring manager name
            output_path: Optional output file path

        Returns:
            Generated email content
        """
        template = self.env.get_template("email_md.j2")

        context = {
            "contact": self.yaml_handler.get_contact(),
            "company_name": company_name,
            "position_name": position_name,
            "hiring_manager_name": hiring_manager_name,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = template.render(**context)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def get_output_path(
        self, variant: str, output_format: str, output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate output file path based on config.

        Args:
            variant: Variant name
            output_format: Output format (md, tex, pdf)
            output_dir: Optional output directory override

        Returns:
            Output file path
        """
        if output_dir is None:
            output_dir = self.config.output_dir

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        date_str = datetime.now().strftime(self.config.get("output.date_format", "%Y-%m-%d"))
        variant_clean = variant.replace(".", "-").replace("_", "-")
        filename = f"resume-{variant_clean}-{date_str}.{output_format}"

        return output_dir / filename

    def list_templates(self) -> list:
        """List available templates."""
        templates = []
        for template_file in self.template_dir.glob("*.j2"):
            templates.append(template_file.stem)
        return templates

    def get_pdf_generator(self) -> Optional["ResumePDFLibGenerator"]:
        """
        Get a PDFGenerator instance from resume-pdf-lib.

        Returns:
            ResumePDFLibGenerator instance if available, None otherwise
        """
        if not RESUME_PDF_LIB_AVAILABLE:
            return None

        try:
            return ResumePDFLibGenerator(templates_dir=str(self.template_dir))
        except Exception:
            return None

    def generate_pdf_with_resume_pdf_lib(
        self,
        output_path: Path,
        variant: str = "base",
    ) -> None:
        """
        Generate PDF using resume-pdf-lib package.

        Args:
            output_path: Output PDF path
            variant: Template variant name

        Raises:
            ImportError: If resume-pdf-lib is not available
            RuntimeError: If PDF generation fails
        """
        if not RESUME_PDF_LIB_AVAILABLE:
            raise ImportError(
                "resume-pdf-lib is not installed. " "Install it with: pip install resume-pdf-lib"
            )

        pdf_gen = self.get_pdf_generator()
        if pdf_gen is None:
            raise RuntimeError("Failed to initialize PDF generator from resume-pdf-lib")

        # Prepare resume data in JSON Resume format
        resume_data = self._prepare_json_resume_format(variant)

        # Generate PDF
        pdf_gen.generate_pdf(resume_data, variant=variant, output_path=str(output_path))

    def _prepare_json_resume_format(self, variant: str) -> Dict[str, Any]:
        """
        Prepare resume data in JSON Resume format for resume-pdf-lib.

        Args:
            variant: Variant name

        Returns:
            Resume data in JSON Resume format
        """
        variant_key = variant.replace("v1.", "").replace("v2.", "").split("-")[0]
        if variant_key.endswith(".0"):
            variant_key = variant_key.split(".")[0] + "." + variant_key.split(".")[1] + ".0"

        # Get variant config to determine summary key
        variant_config = self.yaml_handler.get_variant(variant)
        if not variant_config:
            if "backend" in variant:
                summary_key = "backend"
            elif "ml" in variant or "ai" in variant:
                summary_key = "ml_ai"
            elif "fullstack" in variant or "full" in variant:
                summary_key = "fullstack"
            elif "devops" in variant:
                summary_key = "devops"
            elif "leadership" in variant:
                summary_key = "leadership"
            else:
                summary_key = "base"
        else:
            summary_key = variant_config.get("summary_key", "base")

        contact = self.yaml_handler.get_contact()

        # Build JSON Resume format
        resume_data = {
            "basics": {
                "name": contact.get("name", ""),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "summary": self.yaml_handler.get_summary(summary_key),
            },
            "work": self.yaml_handler.get_experience(variant),
            "education": self.yaml_handler.get_education(variant),
            "skills": self.yaml_handler.get_skills(variant),
            "projects": self.yaml_handler.get_projects(variant),
            "publications": self.yaml_handler.data.get("publications", []),
            "certifications": self.yaml_handler.data.get("certifications", []),
        }

        # Add location if available
        if "location" in contact:
            location = contact["location"]
            resume_data["basics"]["location"] = {
                "city": location.get("city", ""),
                "region": location.get("state", ""),
                "postalCode": location.get("zip", ""),
                "country": location.get("country", ""),
            }

        # Add URLs if available
        if "urls" in contact:
            urls = contact["urls"]
            if "github" in urls:
                resume_data["basics"]["url"] = urls["github"]
            if "linkedin" in urls:
                resume_data["basics"]["profiles"] = [
                    {"network": "LinkedIn", "url": urls["linkedin"]}
                ]

        return resume_data
