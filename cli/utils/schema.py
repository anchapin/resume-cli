"""Schema validation for resume.yaml."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Resume YAML Schema
RESUME_SCHEMA = {
    "meta": {
        "required": True,
        "type": dict,
        "fields": {
            "version": {"required": True, "type": str},
            "last_updated": {"required": True, "type": str},
            "author": {"required": False, "type": str},
        },
    },
    "contact": {
        "required": True,
        "type": dict,
        "fields": {
            "name": {"required": True, "type": str},
            "phone": {"required": True, "type": str},
            "email": {"required": True, "type": str},
            "credentials": {"required": False, "type": list},
            "location": {"required": False, "type": dict},
            "urls": {"required": False, "type": dict},
        },
    },
    "professional_summary": {
        "required": True,
        "type": dict,
        "fields": {
            "base": {"required": True, "type": str},
            "variants": {"required": False, "type": dict},
        },
    },
    "skills": {"required": True, "type": dict, "fields": {}},  # Dynamic categories
    "experience": {
        "required": True,
        "type": list,
        "item_fields": {
            "company": {"required": True, "type": str},
            "title": {"required": True, "type": str},
            "start_date": {"required": True, "type": str},
            "end_date": {"required": False, "type": (str, type(None))},
            "location": {"required": False, "type": str},
            "bullets": {"required": True, "type": list},
        },
    },
    "education": {
        "required": True,
        "type": list,
        "item_fields": {
            "institution": {"required": True, "type": str},
            "degree": {"required": True, "type": str},
            "graduation_date": {"required": True, "type": str},
            "location": {"required": False, "type": str},
            "field": {"required": False, "type": str},
        },
    },
    "publications": {
        "required": False,
        "type": list,
        "item_fields": {
            "authors": {"required": True, "type": str},
            "year": {"required": True, "type": str},
            "title": {"required": True, "type": str},
            "type": {"required": True, "type": str},
            "journal": {"required": False, "type": str},
            "volume": {"required": False, "type": str},
            "pages": {"required": False, "type": str},
            "doi": {"required": False, "type": str},
            "conference": {"required": False, "type": str},
            "location": {"required": False, "type": str},
        },
    },
    "certifications": {"required": False, "type": list},
    "affiliations": {"required": False, "type": list},
    "projects": {"required": False, "type": dict},
    "variants": {
        "required": True,
        "type": dict,
        "fields": {
            # Dynamic variant names
        },
    },
}


class ValidationError:
    """Represents a validation error with actionable guidance."""

    # Error message templates with "What to do" guidance
    ERROR_GUIDANCE = {
        "contact.email": {
            "invalid": 'The email "{value}" is not a valid format.\n\nWhat to do:\n  • Check your email in resume.yaml\n  • Format should be: user@domain.com\n  • Example: john@example.com',
        },
        "contact.name": {
            "missing": 'Missing required "name" field in contact section.\n\nWhat to do:\n  • Add your full name to the contact section in resume.yaml\n  • Example: name: "John Doe"',
        },
        "contact.phone": {
            "missing": 'Missing required "phone" field in contact section.\n\nWhat to do:\n  • Add your phone number to the contact section in resume.yaml\n  • Example: phone: "+1 (555) 123-4567"',
        },
        "root": {
            "file_not_found": '{message}\n\nWhat to do:\n  • Run "resume-cli init --from-existing" to create resume.yaml\n  • Or manually create resume.yaml from the sample template\n  • See: https://github.com/anchapin/resume-cli#getting-started',
            "yaml_error": "{message}\n\nWhat to do:\n  • Check your resume.yaml for syntax errors\n  • Common issues: inconsistent indentation, missing colons, unquoted special characters\n  • Use a YAML validator: https://www.yamllint.com/\n  • See: https://github.com/anchapin/resume-cli#troubleshooting",
        },
        "experience": {
            "missing": 'Missing required "experience" section.\n\nWhat to do:\n  • Add an experience section to resume.yaml\n  • See example: https://github.com/anchapin/resume-cli#adding-a-new-jobexperience',
        },
        "education": {
            "missing": 'Missing required "education" section.\n\nWhat to do:\n  • Add an education section to resume.yaml',
        },
        "skills": {
            "missing": 'Missing required "skills" section.\n\nWhat to do:\n  • Add a skills section to resume.yaml\n  • Example: skills:\n    programming: [Python, JavaScript]\n    tools: [Git, Docker]',
        },
    }

    def __init__(self, path: str, message: str, level: str = "error", guidance: str = None):
        """
        Initialize validation error.

        Args:
            path: Dot-notation path to error location (e.g., "experience.0.company")
            message: Error message
            level: Error level (error, warning, info)
            guidance: Optional actionable guidance message
        """
        self.path = path
        self.message = message
        self.level = level
        self.guidance = guidance

    def __str__(self) -> str:
        level_str = self.level.upper().ljust(7)
        base_msg = f"[{level_str}] {self.path}: {self.message}"
        if self.guidance:
            return f"{base_msg}\n\n{self.guidance}"
        return base_msg

    def __repr__(self) -> str:
        return (
            f"ValidationError(path='{self.path}', message='{self.message}', level='{self.level}')"
        )


class ResumeValidator:
    """Validator for resume.yaml schema."""

    def __init__(self, yaml_path: Optional[Path] = None):
        """
        Initialize validator.

        Args:
            yaml_path: Path to resume.yaml
        """
        from .yaml_parser import ResumeYAML

        self.yaml_handler = ResumeYAML(yaml_path)
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if no errors, False otherwise
        """
        self.errors = []
        self.warnings = []

        try:
            data = self.yaml_handler.load()
        except FileNotFoundError as e:
            self.errors.append(ValidationError("root", str(e), "error"))
            return False
        except yaml.YAMLError as e:
            self.errors.append(ValidationError("root", f"YAML parsing error: {e}", "error"))
            return False

        self._validate_structure(data)
        self._validate_contact(data)
        self._validate_experience(data)
        self._validate_education(data)
        self._validate_variants(data)
        self._validate_dates(data)
        self._validate_email_format(data)

        return len(self.errors) == 0

    def _validate_structure(self, data: Dict[str, Any]) -> None:
        """Validate top-level structure."""
        # Check required top-level keys
        for key, spec in RESUME_SCHEMA.items():
            if spec.get("required", False) and key not in data:
                guidance = self._get_guidance(key, "missing")
                self.errors.append(
                    ValidationError(key, f"Missing required section", "error", guidance)
                )

            # Check type
            if key in data:
                expected_type = spec.get("type")
                if expected_type and not isinstance(data[key], expected_type):
                    self.errors.append(
                        ValidationError(
                            key,
                            f"Expected type {expected_type.__name__}, got {type(data[key]).__name__}",
                            "error",
                        )
                    )

    def _get_guidance(self, path: str, error_type: str = "missing", value: str = None) -> str:
        """Get actionable guidance for an error."""
        key = path
        # Try to get guidance for this path and error type
        if key in self.ERROR_GUIDANCE:
            template = self.ERROR_GUIDANCE[key].get(error_type, "")
            if template:
                if value and "{value}" in template:
                    return template.replace("{value}", value)
                if "{message}" in template:
                    return template.replace("{message}", f"{path}: Missing required section")
                return template

        # Try just the path as the key
        if path in self.ERROR_GUIDANCE:
            template = self.ERROR_GUIDANCE[path].get(error_type, "")
            if template:
                if value and "{value}" in template:
                    return template.replace("{value}", value)
                return template

        return ""

    def _validate_contact(self, data: Dict[str, Any]) -> None:
        """Validate contact information."""
        contact = data.get("contact", {})

        # Check that contact is a dict
        if not isinstance(contact, dict):
            self.errors.append(ValidationError("contact", "Expected type dict", "error"))
            return

        required_fields = ["name", "phone", "email"]

        for field in required_fields:
            if field not in contact or not contact[field]:
                guidance = self._get_guidance(f"contact.{field}", "missing")
                self.errors.append(
                    ValidationError(f"contact.{field}", "Missing required field", "error", guidance)
                )

        # Validate email format
        email = contact.get("email", "")
        if email and "@" not in email:
            guidance = self._get_guidance("contact.email", "invalid", email)
            self.errors.append(
                ValidationError("contact.email", "Invalid email format", "error", guidance)
            )

    def _validate_experience(self, data: Dict[str, Any]) -> None:
        """Validate experience entries."""
        experience = data.get("experience", [])

        for i, job in enumerate(experience):
            prefix = f"experience.{i}"

            # Check required fields
            for field in ["company", "title", "start_date", "bullets"]:
                if field not in job or not job[field]:
                    self.errors.append(
                        ValidationError(f"{prefix}.{field}", "Missing required field", "error")
                    )

            # Check bullets structure
            bullets = job.get("bullets", [])
            if not isinstance(bullets, list):
                self.errors.append(ValidationError(f"{prefix}.bullets", "Must be a list", "error"))
            else:
                for j, bullet in enumerate(bullets):
                    if not isinstance(bullet, dict):
                        self.errors.append(
                            ValidationError(f"{prefix}.bullets.{j}", "Must be a dict", "error")
                        )
                    elif "text" not in bullet:
                        self.errors.append(
                            ValidationError(
                                f"{prefix}.bullets.{j}", "Missing 'text' field", "error"
                            )
                        )

    def _validate_education(self, data: Dict[str, Any]) -> None:
        """Validate education entries."""
        education = data.get("education", [])

        for i, edu in enumerate(education):
            prefix = f"education.{i}"

            # Check required fields
            for field in ["institution", "degree", "graduation_date"]:
                if field not in edu or not edu[field]:
                    self.errors.append(
                        ValidationError(f"{prefix}.{field}", "Missing required field", "error")
                    )

    def _validate_variants(self, data: Dict[str, Any]) -> None:
        """Validate variant configurations."""
        variants = data.get("variants", {})

        if not variants:
            self.warnings.append(ValidationError("variants", "No variants defined", "warning"))
            return

        for variant_name, variant_config in variants.items():
            prefix = f"variants.{variant_name}"

            # Check required fields
            for field in ["description", "skill_sections"]:
                if field not in variant_config:
                    self.warnings.append(
                        ValidationError(f"{prefix}.{field}", "Missing recommended field", "warning")
                    )

            # Validate skill_sections exist
            skill_sections = variant_config.get("skill_sections", [])
            all_skills = data.get("skills", {})
            for section in skill_sections:
                if section not in all_skills:
                    self.errors.append(
                        ValidationError(
                            f"{prefix}.skill_sections.{section}",
                            f"Skill section '{section}' not defined in skills",
                            "error",
                        )
                    )

    def _validate_dates(self, data: Dict[str, Any]) -> None:
        """Validate date formats."""
        from datetime import datetime

        # Check meta.last_updated
        last_updated = data.get("meta", {}).get("last_updated", "")
        if last_updated:
            try:
                datetime.strptime(last_updated, "%Y-%m-%d")
            except ValueError:
                self.errors.append(
                    ValidationError(
                        "meta.last_updated", "Invalid date format (expected YYYY-MM-DD)", "error"
                    )
                )

        # Check experience dates
        experience = data.get("experience", [])
        for i, job in enumerate(experience):
            for date_field in ["start_date", "end_date"]:
                date_val = job.get(date_field)
                if date_val and date_val is not None:
                    try:
                        # Accept YYYY-MM or YYYY-MM-DD
                        if len(date_val) == 7:
                            datetime.strptime(date_val, "%Y-%m")
                        elif len(date_val) == 10:
                            datetime.strptime(date_val, "%Y-%m-%d")
                        else:
                            self.errors.append(
                                ValidationError(
                                    f"experience.{i}.{date_field}",
                                    "Invalid date format (expected YYYY-MM or YYYY-MM-DD)",
                                    "error",
                                )
                            )
                    except ValueError:
                        self.errors.append(
                            ValidationError(
                                f"experience.{i}.{date_field}", "Invalid date format", "error"
                            )
                        )

    def _validate_email_format(self, data: Dict[str, Any]) -> None:
        """Validate email formats."""
        contact = data.get("contact")
        if not isinstance(contact, dict):
            return
        email = contact.get("email", "")
        if email:
            # Basic email validation
            if "@" not in email or "." not in email.split("@")[-1]:
                self.errors.append(
                    ValidationError("contact.email", "Invalid email format", "error")
                )

    def print_results(self) -> None:
        """Print validation results to stdout."""
        if not self.errors and not self.warnings:
            print("✅ Resume validation passed with no errors or warnings!")
            return

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
            print(f"\n❌ Validation failed with {len(self.errors)} error(s)")
        else:
            print(f"\n✅ Validation passed with {len(self.warnings)} warning(s)")


def validate_resume(yaml_path: Optional[Path] = None) -> bool:
    """
    Validate resume.yaml.

    Args:
        yaml_path: Path to resume.yaml

    Returns:
        True if valid, False otherwise
    """
    validator = ResumeValidator(yaml_path)
    is_valid = validator.validate_all()
    validator.print_results()
    return is_valid


if __name__ == "__main__":
    # Run validation when executed directly
    import sys

    yaml_path = sys.argv[1] if len(sys.argv) > 1 else None
    is_valid = validate_resume(yaml_path)
    sys.exit(0 if is_valid else 1)
