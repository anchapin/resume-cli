"""TXT resume generator for ATS-friendly plain text output."""

from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.config import Config
from ..utils.yaml_parser import ResumeYAML


class TxtGenerator:
    """Generate ATS-friendly plain text resumes."""

    # ASCII-safe separators for ATS compatibility
    SECTION_SEPARATOR = "=" * 80
    SUBSECTION_SEPARATOR = "-" * 40

    def __init__(
        self,
        yaml_path: Optional[Path] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize TXT generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.yaml_handler = ResumeYAML(yaml_path)
        self.config = config or Config()

    def generate(
        self,
        variant: str,
        output_path: Optional[Path] = None,
        enhanced_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate resume as plain text.

        Args:
            variant: Variant name (e.g., "v1.0.0-backend")
            output_path: Optional output file path
            enhanced_context: Optional dict with AI-enhanced data

        Returns:
            Generated text content
        """
        # Determine summary key
        variant_key = variant.replace("v1.", "").replace("v2.", "").split("-")[0]
        if variant_key.endswith(".0"):
            variant_key = variant_key.split(".")[0] + "." + variant_key.split(".")[1] + ".0"

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

        # Extract technologies for prioritization
        prioritize_technologies = None
        if enhanced_context:
            enhanced_projects = enhanced_context.get("projects", {}).get("featured", [])
            if enhanced_projects:
                all_techs = set()
                for proj in enhanced_projects:
                    if proj.get("highlighted_technologies"):
                        all_techs.update(proj["highlighted_technologies"])
                if all_techs:
                    prioritize_technologies = list(all_techs)

        # Get resume data
        contact = self.yaml_handler.get_contact()
        summary = self.yaml_handler.get_summary(summary_key)
        skills = self.yaml_handler.get_skills(
            variant, prioritize_technologies=prioritize_technologies
        )
        experience = self.yaml_handler.get_experience(variant)
        education = self.yaml_handler.get_education(variant)
        publications = self.yaml_handler.data.get("publications", [])
        certifications = self.yaml_handler.data.get("certifications", [])

        # Merge enhanced context if provided
        if enhanced_context:
            if "summary" in enhanced_context:
                summary = enhanced_context["summary"]
            if "projects" in enhanced_context:
                # Handle enhanced projects structure
                projects = enhanced_context["projects"]
                if isinstance(projects, dict) and "featured" in projects:
                    # Convert to expected format
                    projects_data = {"featured": projects["featured"]}
                else:
                    projects_data = projects
            else:
                projects_data = self.yaml_handler.get_projects(variant)
        else:
            projects_data = self.yaml_handler.get_projects(variant)

        # Build text content
        lines = []

        # Add header
        lines.extend(self._build_header(contact))

        # Add summary
        lines.extend(self._build_summary(summary))

        # Add projects
        lines.extend(self._build_projects(projects_data))

        # Add experience
        lines.extend(self._build_experience(experience))

        # Add education
        lines.extend(self._build_education(education))

        # Add skills
        lines.extend(self._build_skills(skills))

        # Add publications
        lines.extend(self._build_publications(publications))

        # Add certifications
        lines.extend(self._build_certifications(certifications))

        # Join lines and clean up
        content = "\n".join(lines)

        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        return content

    def _build_header(self, contact: Dict) -> list:
        """Build contact information header."""
        lines = []

        # Name and credentials
        name = contact.get("name", "")
        if name:
            lines.append(name)
            credentials = contact.get("credentials", [])
            if credentials:
                lines.append(", ".join(credentials))
            lines.append("")

        # Location
        location_parts = []
        location = contact.get("location", {})
        if location.get("city"):
            location_parts.append(location["city"])
        if location.get("state"):
            location_parts.append(location["state"])
        if location.get("zip"):
            location_parts.append(location["zip"])

        # Contact info line
        contact_line = []
        if location_parts:
            contact_line.append(", ".join(location_parts))
        if contact.get("email"):
            contact_line.append(contact.get("email"))
        if contact.get("phone"):
            contact_line.append(contact.get("phone"))

        if contact_line:
            lines.append(" | ".join(contact_line))

        # URLs
        urls = []
        urls_dict = contact.get("urls", {})
        if urls_dict.get("github"):
            urls.append(urls_dict["github"])
        if urls_dict.get("linkedin"):
            urls.append(urls_dict["linkedin"])
        if urls_dict.get("website"):
            urls.append(urls_dict["website"])

        if urls:
            lines.append(" | ".join(urls))

        lines.append("")
        lines.append(self.SECTION_SEPARATOR)
        lines.append("")

        return lines

    def _build_section_heading(self, title: str) -> list:
        """Build a section heading."""
        return ["", title.upper(), ""]

    def _build_summary(self, summary: Optional[Dict]) -> list:
        """Build professional summary section."""
        if not summary:
            return []

        lines = self._build_section_heading("PROFESSIONAL SUMMARY")

        summary_text = summary.get("content", "") if isinstance(summary, dict) else str(summary)
        if summary_text:
            # Wrap text to reasonable width for ATS
            lines.extend(self._wrap_text(summary_text, width=80))
            lines.append("")

        return lines

    def _build_projects(self, projects: Dict) -> list:
        """Build projects section."""
        if not projects:
            return []

        lines = self._build_section_heading("PROJECTS")

        for category, project_list in projects.items():
            # Category heading
            category_title = category.replace("_", " ").title()
            if category_title.lower() in ["ai ml", "ai_ml"]:
                category_title = "AI/ML"

            lines.append(category_title)
            lines.append("")

            for project in project_list:
                # Project name
                project_name = project.get("name", "")
                if project_name:
                    lines.append(f"- {project_name}")

                # Description
                description = project.get("enhanced_description") or project.get("description", "")
                if description:
                    lines.extend(self._wrap_text(description, width=78, indent="  "))

                # URL
                url = project.get("url")
                if url:
                    lines.append(f"  URL: {url}")

                # Technologies
                techs = project.get("highlighted_technologies", [])
                if techs:
                    lines.append(f"  Technologies: {', '.join(techs)}")

                # Achievements
                achievements = project.get("achievement_highlights", [])
                for achievement in achievements:
                    lines.append(f"  - {achievement}")

                lines.append("")

        return lines

    def _build_experience(self, experience: list) -> list:
        """Build work experience section."""
        if not experience:
            return []

        lines = self._build_section_heading("PROFESSIONAL EXPERIENCE")

        for job in experience:
            # Job title and company
            title = job.get("title", "")
            company = job.get("company", "")
            location = job.get("location", "")

            header_text = title
            if company:
                header_text += f" | {company}"
            if location:
                header_text += f" | {location}"

            if header_text:
                lines.append(header_text)

            # Dates
            start_date = job.get("start_date", "")
            end_date = job.get("end_date", "")
            if start_date:
                date_text = f"{start_date} - {end_date if end_date else 'Present'}"
                lines.append(date_text)
                lines.append("")

            # Bullets
            bullets = job.get("bullets", [])
            for bullet in bullets:
                bullet_text = bullet.get("text", "") if isinstance(bullet, dict) else str(bullet)
                if bullet_text:
                    lines.extend(self._wrap_text(f"- {bullet_text}", width=78, indent="  "))

            lines.append("")

        return lines

    def _build_education(self, education: list) -> list:
        """Build education section."""
        if not education:
            return []

        lines = self._build_section_heading("EDUCATION")

        for edu in education:
            # Institution and location
            institution = edu.get("institution", "")
            location = edu.get("location", "")

            header_text = institution
            if location:
                header_text += f" | {location}"

            if header_text:
                lines.append(header_text)

            # Degree
            degree = edu.get("degree", "")
            field = edu.get("field", "")
            graduation_date = edu.get("graduation_date", "")

            degree_text = degree
            if field:
                degree_text += f", {field}"
            if graduation_date:
                degree_text += f" | Graduated {graduation_date}"

            if degree_text:
                lines.append(f"  {degree_text}")

            lines.append("")

        return lines

    def _build_skills(self, skills: Dict) -> list:
        """Build skills section."""
        if not skills:
            return []

        lines = self._build_section_heading("SKILLS")

        for section_name, skill_list in skills.items():
            # Section header
            section_title = section_name.replace("_", " ").title()

            # Skills
            skill_texts = []
            for skill in skill_list:
                if isinstance(skill, dict):
                    skill_text = skill.get("name", "")
                    if skill.get("level"):
                        skill_text += f" ({skill['level']})"
                else:
                    skill_text = str(skill)
                if skill_text:
                    skill_texts.append(skill_text)

            if skill_texts:
                lines.append(f"{section_title}: {', '.join(skill_texts)}")

        lines.append("")

        return lines

    def _build_publications(self, publications: list) -> list:
        """Build publications section."""
        if not publications:
            return []

        lines = self._build_section_heading("PUBLICATIONS")

        for pub in publications:
            pub.get("type", "")
            title = pub.get("title", "")
            authors = pub.get("authors", "")
            year = pub.get("year", "")
            journal = pub.get("journal", "")
            conference = pub.get("conference", "")

            # Format publication entry
            parts = []
            if authors:
                parts.append(authors)
            if year:
                parts.append(f"({year})")
            if title:
                parts.append(f'"{title}."')

            if journal:
                parts.append(journal)
            elif conference:
                parts.append(f"In {conference}")

            if parts:
                lines.append(f"- {' '.join(parts)}")

        lines.append("")

        return lines

    def _build_certifications(self, certifications: list) -> list:
        """Build certifications section."""
        if not certifications:
            return []

        lines = self._build_section_heading("CERTIFICATIONS")

        for cert in certifications:
            cert_name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            license_num = cert.get("license_number", "")

            text = cert_name
            if issuer:
                text += f" - {issuer}"
            if license_num:
                text += f" (License: {license_num})"

            if text:
                lines.append(f"- {text}")

        lines.append("")

        return lines

    def _wrap_text(self, text: str, width: int = 80, indent: str = "") -> list:
        """Wrap text to specified width with optional indent."""
        lines = []
        words = text.split()
        current_line = indent

        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                if current_line == indent:
                    current_line += word
                else:
                    current_line += " " + word
            else:
                if current_line != indent:
                    lines.append(current_line)
                current_line = indent + word

        if current_line != indent:
            lines.append(current_line)

        return lines
