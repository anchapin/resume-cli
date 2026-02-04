"""YAML parser utility for resume data."""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from datetime import datetime


class ResumeYAML:
    """Handler for reading and writing resume.yaml."""

    def __init__(self, yaml_path: Optional[Path] = None):
        """
        Initialize YAML handler.

        Args:
            yaml_path: Path to resume.yaml. Defaults to ../resume.yaml from cli/ dir
        """
        if yaml_path is None:
            # Default to resume.yaml in parent directory
            yaml_path = Path(__file__).parent.parent.parent / "resume.yaml"

        self.yaml_path = Path(yaml_path)
        self._data: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        Load resume data from YAML file.

        Returns:
            Parsed YAML data as dictionary

        Raises:
            FileNotFoundError: If resume.yaml doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        if not self.yaml_path.exists():
            raise FileNotFoundError(
                f"Resume file not found: {self.yaml_path}\n"
                f"Run 'resume-cli init' to create it."
            )

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

        return self._data

    @property
    def data(self) -> Dict[str, Any]:
        """Get cached data, loading if necessary."""
        if self._data is None:
            self.load()
        return self._data

    def save(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Save resume data to YAML file.

        Args:
            data: Data to save. If None, saves current cached data.
        """
        if data is not None:
            self._data = data
        elif self._data is None:
            raise ValueError("No data to save. Load or provide data first.")

        # Update last_updated timestamp
        if "meta" in self._data:
            self._data["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def get_contact(self) -> Dict[str, Any]:
        """Get contact information."""
        return self.data.get("contact", {})

    def get_summary(self, variant: str = "base") -> str:
        """
        Get professional summary for a variant.

        Args:
            variant: Variant key (base, fullstack, backend, etc.)

        Returns:
            Summary text for the variant
        """
        summaries = self.data.get("professional_summary", {})
        if variant == "base" or variant not in summaries.get("variants", {}):
            return summaries.get("base", "")
        return summaries.get("variants", {}).get(variant, summaries.get("base", ""))

    def get_skills(self, variant: Optional[str] = None) -> Dict[str, list]:
        """
        Get skills, optionally filtered by variant.

        Args:
            variant: Variant name to filter skills. Returns all if None.

        Returns:
            Dictionary of skill categories
        """
        all_skills = self.data.get("skills", {})

        if variant is None:
            return all_skills

        # Get variant config
        variant_config = self.data.get("variants", {}).get(variant, {})
        skill_sections = variant_config.get("skill_sections", list(all_skills.keys()))

        # Filter and reorder skills
        filtered_skills = {}
        for section in skill_sections:
            if section in all_skills:
                # Filter skills by emphasize_for
                section_skills = all_skills[section]
                if isinstance(section_skills, list):
                    filtered_skills[section] = [
                        s for s in section_skills
                        if (isinstance(s, dict) and variant in s.get("emphasize_for", [variant])) or
                           (isinstance(s, str))
                    ]
                else:
                    filtered_skills[section] = section_skills

        return filtered_skills

    def get_experience(self, variant: Optional[str] = None) -> list:
        """
        Get experience entries, optionally filtered by variant.

        Args:
            variant: Variant name to filter bullets

        Returns:
            List of experience entries
        """
        experience = self.data.get("experience", [])

        if variant is None:
            return experience

        variant_config = self.data.get("variants", {}).get(variant, {})
        max_bullets = variant_config.get("max_bullets_per_job", 4)
        emphasize_keywords = variant_config.get("emphasize_keywords", [])

        filtered_exp = []
        for job in experience:
            job_copy = job.copy()
            bullets = job.get("bullets", [])

            # Filter bullets by emphasize_for or keywords
            filtered_bullets = []
            for bullet in bullets:
                emphasize_for = bullet.get("emphasize_for", [])
                text = bullet.get("text", "")

                # Include if variant is emphasized or keywords match
                if (variant in emphasize_for or
                    any(kw.lower() in text.lower() for kw in emphasize_keywords)):
                    filtered_bullets.append(bullet)

            # Limit bullets and preserve order
            if len(filtered_bullets) > max_bullets:
                filtered_bullets = filtered_bullets[:max_bullets]

            # Fallback: if no bullets matched, include first max_bullets
            if not filtered_bullets and bullets:
                filtered_bullets = bullets[:max_bullets]

            job_copy["bullets"] = filtered_bullets
            filtered_exp.append(job_copy)

        return filtered_exp

    def get_education(self, variant: Optional[str] = None) -> list:
        """
        Get education entries.

        Args:
            variant: Variant name (currently unused, for future expansion)

        Returns:
            List of education entries
        """
        education = self.data.get("education", [])

        if variant is None:
            return education

        # Future: could filter/reorder education by variant
        variant_config = self.data.get("variants", {}).get(variant, {})
        return education

    def get_projects(self, variant: Optional[str] = None) -> Dict[str, list]:
        """
        Get projects by category.

        Args:
            variant: Variant name to filter categories

        Returns:
            Dictionary of project categories
        """
        all_projects = self.data.get("projects", {})

        if variant is None:
            return all_projects

        variant_config = self.data.get("variants", {}).get(variant, {})
        categories = variant_config.get("project_categories", list(all_projects.keys()))

        filtered_projects = {}
        for cat in categories:
            if cat in all_projects:
                filtered_projects[cat] = all_projects[cat]

        return filtered_projects

    def get_variants(self) -> Dict[str, Dict[str, Any]]:
        """Get all available variants."""
        return self.data.get("variants", {})

    def get_variant(self, variant_name: str) -> Optional[Dict[str, Any]]:
        """Get specific variant configuration."""
        return self.data.get("variants", {}).get(variant_name)

    def list_variants(self) -> list:
        """List all variant names."""
        return list(self.data.get("variants", {}).keys())
