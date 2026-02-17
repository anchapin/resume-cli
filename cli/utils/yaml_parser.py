"""YAML parser utility for resume data."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


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
                f"Resume file not found: {self.yaml_path}\n" f"Run 'resume-cli init' to create it."
            )

        import yaml

        with open(self.yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self._data = data if isinstance(data, dict) else {}

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

        # Create parent directories if needed
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

        import yaml

        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def get_contact(self) -> Dict[str, Any]:
        """Get contact information."""
        contact = self.data.get("contact", {})
        return contact if isinstance(contact, dict) else {}

    def get_summary(self, variant: str = "base") -> str:
        """
        Get professional summary for a variant.

        Args:
            variant: Variant key (base, fullstack, backend, etc.)

        Returns:
            Summary text for the variant
        """
        summaries = self.data.get("professional_summary", {})
        if not isinstance(summaries, dict):
            return ""
        if variant == "base" or variant not in summaries.get("variants", {}):
            return str(summaries.get("base", ""))
        variants = summaries.get("variants", {})
        if isinstance(variants, dict):
            return str(variants.get(variant, summaries.get("base", "")))
        return str(summaries.get("base", ""))

    def get_skills(
        self, variant: Optional[str] = None, prioritize_technologies: Optional[list] = None
    ) -> Dict[str, list]:
        """
        Get skills, optionally filtered by variant.

        Args:
            variant: Variant name to filter skills. Returns all if None.
            prioritize_technologies: Optional list of technologies to prioritize (move to front of lists)

        Returns:
            Dictionary of skill categories
        """
        all_skills = self.data.get("skills", {})
        if not isinstance(all_skills, dict):
            return {}

        filtered_skills: Dict[str, list]
        if variant is None:
            filtered_skills = all_skills
        else:
            # Get variant config
            variants = self.data.get("variants", {})
            variant_config = variants.get(variant, {}) if isinstance(variants, dict) else {}
            skill_sections = variant_config.get("skill_sections", list(all_skills.keys()))

            # Filter and reorder skills
            filtered_skills = {}
            for section in skill_sections:
                if section in all_skills:
                    # Filter skills by emphasize_for
                    section_skills = all_skills[section]
                    if isinstance(section_skills, list):
                        filtered_skills[section] = [
                            s
                            for s in section_skills
                            if (
                                isinstance(s, dict) and variant in s.get("emphasize_for", [variant])
                            )
                            or (isinstance(s, str))
                        ]
                    elif isinstance(section_skills, list):  # Make mypy happy about list type
                        filtered_skills[section] = section_skills

        # Apply technology prioritization if specified
        if prioritize_technologies and filtered_skills:
            filtered_skills = self._prioritize_skills(filtered_skills, prioritize_technologies)

        return filtered_skills

    def _prioritize_skills(self, skills: Dict[str, list], technologies: list) -> Dict[str, list]:
        """
        Reorder skills within categories to prioritize highlighted technologies.

        Args:
            skills: Dictionary of skill categories
            technologies: List of technology names to prioritize (case-insensitive)

        Returns:
            Dictionary with same structure, but matching skills moved to front of each list
        """
        prioritized = {}
        tech_lower = [t.lower() for t in technologies]

        for section, section_skills in skills.items():
            if not isinstance(section_skills, list):
                prioritized[section] = section_skills
                continue

            # Separate skills into matching and non-matching
            matching = []
            non_matching = []

            for skill in section_skills:
                skill_name = skill if isinstance(skill, str) else skill.get("name", "")

                # Check if skill matches any of the technologies
                if any(tech in skill_name.lower() for tech in tech_lower):
                    matching.append(skill)
                else:
                    non_matching.append(skill)

            # Combine with matching skills first
            prioritized[section] = matching + non_matching

        return prioritized

    def get_experience(self, variant: Optional[str] = None) -> list:
        """
        Get experience entries, optionally filtered by variant.

        Args:
            variant: Variant name to filter bullets

        Returns:
            List of experience entries
        """
        experience = self.data.get("experience", [])
        if not isinstance(experience, list):
            return []

        if variant is None:
            return experience

        variants = self.data.get("variants", {})
        variant_config = variants.get(variant, {}) if isinstance(variants, dict) else {}
        max_bullets = variant_config.get("max_bullets_per_job", 4)
        emphasize_keywords = variant_config.get("emphasize_keywords", [])

        filtered_exp = []
        for job in experience:
            if not isinstance(job, dict):
                continue
            job_copy = job.copy()
            bullets = job.get("bullets", [])

            # Filter bullets by emphasize_for or keywords
            filtered_bullets = []
            for bullet in bullets:
                if not isinstance(bullet, dict):
                    continue
                emphasize_for = bullet.get("emphasize_for", [])
                text = bullet.get("text", "")

                # Include if variant is emphasized or keywords match
                if variant in emphasize_for or any(
                    kw.lower() in text.lower() for kw in emphasize_keywords
                ):
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
        if not isinstance(education, list):
            return []

        if variant is None:
            return education

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
        if not isinstance(all_projects, dict):
            return {}

        if variant is None:
            return all_projects

        variants = self.data.get("variants", {})
        variant_config = variants.get(variant, {}) if isinstance(variants, dict) else {}
        categories = variant_config.get("project_categories", list(all_projects.keys()))

        filtered_projects = {}
        for cat in categories:
            if cat in all_projects:
                filtered_projects[cat] = all_projects[cat]

        return filtered_projects

    def get_variants(self) -> Dict[str, Dict[str, Any]]:
        """Get all available variants."""
        variants = self.data.get("variants", {})
        return variants if isinstance(variants, dict) else {}

    def get_variant(self, variant_name: str) -> Optional[Dict[str, Any]]:
        """Get specific variant configuration."""
        variants = self.data.get("variants", {})
        if isinstance(variants, dict):
            return variants.get(variant_name)
        return None

    def list_variants(self) -> list:
        """List all variant names."""
        return list(self.data.get("variants", {}).keys())
