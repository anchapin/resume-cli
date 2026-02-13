"""Unit tests for ResumeValidator class."""

import os
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from cli.utils.schema import RESUME_SCHEMA, ResumeValidator, ValidationError, validate_resume


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_initialization(self):
        """Test ValidationError initialization."""
        error = ValidationError("test.path", "Test message", "warning")

        assert error.path == "test.path"
        assert error.message == "Test message"
        assert error.level == "warning"

    def test_validation_error_str(self):
        """Test ValidationError __str__ method."""
        error = ValidationError("test.path", "Test message", "error")
        error_str = str(error)

        assert "[ERROR]" in error_str
        assert "test.path" in error_str
        assert "Test message" in error_str

    def test_validation_error_repr(self):
        """Test ValidationError __repr__ method."""
        error = ValidationError("test.path", "Test message", "info")
        error_repr = repr(error)

        assert "ValidationError" in error_repr
        assert "test.path" in error_repr
        assert "Test message" in error_repr
        assert "info" in error_repr


class TestResumeValidatorInitialization:
    """Test ResumeValidator initialization."""

    def test_init_with_path(self, sample_yaml_file: Path):
        """Test initialization with yaml path."""
        validator = ResumeValidator(sample_yaml_file)

        assert validator.yaml_handler.yaml_path == sample_yaml_file
        assert validator.errors == []
        assert validator.warnings == []


class TestResumeValidatorValidateAll:
    """Test validate_all method."""

    def test_validate_all_valid_resume(self, sample_yaml_file: Path):
        """Test validate_all passes for valid resume."""
        validator = ResumeValidator(sample_yaml_file)
        is_valid = validator.validate_all()

        assert is_valid is True
        assert len(validator.errors) == 0

    def test_validate_all_file_not_found(self, temp_dir: Path):
        """Test validate_all handles missing file."""
        validator = ResumeValidator(temp_dir / "nonexistent.yaml")
        is_valid = validator.validate_all()

        assert is_valid is False
        assert len(validator.errors) > 0
        assert "Resume file not found" in validator.errors[0].message

    def test_validate_all_invalid_yaml(self, temp_dir: Path):
        """Test validate_all handles malformed YAML."""
        invalid_yaml = temp_dir / "invalid.yaml"
        with open(invalid_yaml, "w") as f:
            f.write("invalid: yaml: [unclosed")

        validator = ResumeValidator(invalid_yaml)
        is_valid = validator.validate_all()

        assert is_valid is False
        assert len(validator.errors) > 0
        assert "YAML parsing error" in validator.errors[0].message

    def test_validate_all_missing_required_section(self, temp_dir: Path):
        """Test validate_all detects missing required section."""
        invalid_yaml = temp_dir / "no_meta.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        assert any(e.path == "meta" for e in validator.errors)

    def test_validate_all_clears_previous_results(self, sample_yaml_file: Path):
        """Test validate_all clears previous errors/warnings."""
        validator = ResumeValidator(sample_yaml_file)

        # Manually add error
        validator.errors.append(ValidationError("test", "test"))

        # Validate should clear
        validator.validate_all()

        # Error should be cleared (sample data is valid)
        assert len([e for e in validator.errors if e.path == "test"]) == 0


class TestValidateStructure:
    """Test _validate_structure method."""

    def test_validate_structure_valid(self, sample_yaml_file: Path):
        """Test structure validation for valid data."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        # No structure errors for valid resume
        structure_errors = [e for e in validator.errors if "." not in e.path]
        assert len(structure_errors) == 0

    def test_validate_structure_missing_required(self, temp_dir: Path):
        """Test structure validation detects missing required fields."""
        invalid_yaml = temp_dir / "missing_required.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        # Should have errors for missing meta, professional_summary, etc.
        required_missing = [e.path for e in validator.errors]
        assert "meta" in required_missing
        assert "contact" not in required_missing  # Contact is present
        assert "professional_summary" in required_missing

    def test_validate_structure_wrong_type(self, temp_dir: Path):
        """Test structure validation detects wrong type."""
        invalid_yaml = temp_dir / "wrong_type.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {"contact": "not a dict", "professional_summary": "not a dict"}, f  # Should be dict
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        contact_errors = [e for e in validator.errors if e.path == "contact"]
        assert len(contact_errors) > 0
        assert "Expected type dict" in contact_errors[0].message


class TestValidateContact:
    """Test _validate_contact method."""

    def test_validate_contact_valid(self, sample_yaml_file: Path):
        """Test contact validation for valid data."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        contact_errors = [e for e in validator.errors if e.path.startswith("contact.")]
        assert len(contact_errors) == 0

    def test_validate_contact_missing_name(self, temp_dir: Path):
        """Test contact validation detects missing name."""
        invalid_yaml = temp_dir / "no_name.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"email": "test@example.com"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        name_errors = [e for e in validator.errors if e.path == "contact.name"]
        assert len(name_errors) > 0

    def test_validate_contact_missing_email(self, temp_dir: Path):
        """Test contact validation detects missing email."""
        invalid_yaml = temp_dir / "no_email.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        email_errors = [e for e in validator.errors if e.path == "contact.email"]
        assert len(email_errors) > 0

    def test_validate_contact_invalid_email(self, temp_dir: Path):
        """Test contact validation detects invalid email format."""
        invalid_yaml = temp_dir / "invalid_email.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test", "email": "invalid-email"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        email_errors = [e for e in validator.errors if e.path == "contact.email"]
        assert len(email_errors) > 0
        assert "Invalid email format" in email_errors[0].message


class TestValidateExperience:
    """Test _validate_experience method."""

    def test_validate_experience_valid(self, sample_yaml_file: Path):
        """Test experience validation for valid data."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        exp_errors = [e for e in validator.errors if e.path.startswith("experience.")]
        assert len(exp_errors) == 0

    def test_validate_experience_missing_company(self, temp_dir: Path):
        """Test experience validation detects missing company."""
        invalid_yaml = temp_dir / "no_company.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {"experience": [{"title": "Engineer", "start_date": "2020-01", "bullets": []}]}, f
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        company_errors = [e for e in validator.errors if "company" in e.path]
        assert len(company_errors) > 0

    def test_validate_experience_missing_bullets(self, temp_dir: Path):
        """Test experience validation detects missing bullets."""
        invalid_yaml = temp_dir / "no_bullets.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {"experience": [{"company": "Test", "title": "Engineer", "start_date": "2020-01"}]},
                f,
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        bullets_errors = [e for e in validator.errors if "bullets" in e.path]
        assert len(bullets_errors) > 0

    def test_validate_experience_bullets_not_list(self, temp_dir: Path):
        """Test experience validation detects bullets not a list."""
        invalid_yaml = temp_dir / "bullets_not_list.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {
                    "experience": [
                        {
                            "company": "Test",
                            "title": "Engineer",
                            "start_date": "2020-01",
                            "bullets": "not a list",
                        }
                    ]
                },
                f,
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        bullets_errors = [e for e in validator.errors if "bullets" in e.path]
        assert len(bullets_errors) > 0
        assert "Must be a list" in bullets_errors[0].message

    def test_validate_experience_bullet_missing_text(self, temp_dir: Path):
        """Test experience validation detects bullet without text."""
        invalid_yaml = temp_dir / "bullet_no_text.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {
                    "experience": [
                        {
                            "company": "Test",
                            "title": "Engineer",
                            "start_date": "2020-01",
                            "bullets": [{"skills": ["Python"]}],  # Missing text
                        }
                    ]
                },
                f,
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        text_errors = [e for e in validator.errors if "text" in e.path]
        assert len(text_errors) > 0
        assert "Missing 'text' field" in text_errors[0].message


class TestValidateEducation:
    """Test _validate_education method."""

    def test_validate_education_valid(self, sample_yaml_file: Path):
        """Test education validation for valid data."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        edu_errors = [e for e in validator.errors if e.path.startswith("education.")]
        assert len(edu_errors) == 0

    def test_validate_education_missing_institution(self, temp_dir: Path):
        """Test education validation detects missing institution."""
        invalid_yaml = temp_dir / "no_institution.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"education": [{"degree": "BS", "graduation_date": "2020-01"}]}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        inst_errors = [e for e in validator.errors if "institution" in e.path]
        assert len(inst_errors) > 0

    def test_validate_education_missing_graduation_date(self, temp_dir: Path):
        """Test education validation detects missing graduation_date."""
        invalid_yaml = temp_dir / "no_grad_date.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"education": [{"institution": "University", "degree": "BS"}]}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        grad_errors = [e for e in validator.errors if "graduation_date" in e.path]
        assert len(grad_errors) > 0


class TestValidateVariants:
    """Test _validate_variants method."""

    def test_validate_variants_valid(self, sample_yaml_file: Path):
        """Test variants validation for valid data."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        variant_warnings = [w for w in validator.warnings if w.path.startswith("variants.")]
        assert len(variant_warnings) == 0

    def test_validate_variants_no_variants(self, temp_dir: Path):
        """Test variants validation warns when no variants defined."""
        invalid_yaml = temp_dir / "no_variants.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"meta": {"version": "1.0"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        variant_warnings = [w for w in validator.warnings if w.path == "variants"]
        assert len(variant_warnings) > 0
        assert "No variants defined" in variant_warnings[0].message

    def test_validate_variants_missing_skill_sections(self, temp_dir: Path):
        """Test variants validation warns about missing skill_sections."""
        invalid_yaml = temp_dir / "variant_no_skills.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {
                    "meta": {"version": "1.0"},
                    "skills": {"programming": ["Python"]},
                    "variants": {
                        "test": {"description": "Test", "skill_sections": ["nonexistent"]}
                    },
                },
                f,
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        # Should warn about skill_sections
        skill_warnings = [w for w in validator.warnings if "skill_sections" in w.path]
        assert len(skill_warnings) > 0


class TestValidateDates:
    """Test _validate_dates method."""

    def test_validate_dates_valid(self, sample_yaml_file: Path):
        """Test date validation for valid dates."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        date_errors = [e for e in validator.errors if "date" in e.path]
        assert len(date_errors) == 0

    def test_validate_dates_invalid_last_updated(self, temp_dir: Path):
        """Test date validation detects invalid last_updated."""
        invalid_yaml = temp_dir / "invalid_date.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"meta": {"version": "1.0", "last_updated": "2024-13-45"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        date_errors = [e for e in validator.errors if "last_updated" in e.path]
        assert len(date_errors) > 0

    def test_validate_dates_invalid_experience_date(self, temp_dir: Path):
        """Test date validation detects invalid experience dates."""
        invalid_yaml = temp_dir / "invalid_exp_date.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump(
                {
                    "experience": [
                        {
                            "company": "Test",
                            "title": "Engineer",
                            "start_date": "not-a-date",
                            "bullets": [],
                        }
                    ]
                },
                f,
            )

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        date_errors = [e for e in validator.errors if "start_date" in e.path]
        assert len(date_errors) > 0

    def test_validate_dates_accepts_mm_format(self, temp_dir: Path):
        """Test date validation accepts YYYY-MM format."""
        valid_yaml = temp_dir / "valid_mm.yaml"
        with open(valid_yaml, "w") as f:
            yaml.dump(
                {
                    "meta": {"version": "1.0", "last_updated": "2024-01"},
                    "experience": [
                        {
                            "company": "Test",
                            "title": "Engineer",
                            "start_date": "2020-01",  # MM format
                            "bullets": [],
                        }
                    ],
                },
                f,
            )

        validator = ResumeValidator(valid_yaml)
        validator.validate_all()

        date_errors = [e for e in validator.errors if "date" in e.path]
        assert len(date_errors) == 0

    def test_validate_dates_accepts_mmdd_format(self, temp_dir: Path):
        """Test date validation accepts YYYY-MM-DD format."""
        valid_yaml = temp_dir / "valid_mmdd.yaml"
        with open(valid_yaml, "w") as f:
            yaml.dump(
                {
                    "meta": {"version": "1.0", "last_updated": "2024-01-15"},
                    "experience": [
                        {
                            "company": "Test",
                            "title": "Engineer",
                            "start_date": "2020-06-15",  # MM-DD format
                            "bullets": [],
                        }
                    ],
                },
                f,
            )

        validator = ResumeValidator(valid_yaml)
        validator.validate_all()

        date_errors = [e for e in validator.errors if "date" in e.path]
        assert len(date_errors) == 0


class TestValidateEmailFormat:
    """Test _validate_email_format method."""

    def test_validate_email_format_valid(self, sample_yaml_file: Path):
        """Test email validation for valid format."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()

        email_errors = [e for e in validator.errors if "email" in e.path]
        assert len(email_errors) == 0

    def test_validate_email_format_missing_at_sign(self, temp_dir: Path):
        """Test email validation detects missing @ sign."""
        invalid_yaml = temp_dir / "no_at.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test", "email": "invalidemail.com"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        email_errors = [e for e in validator.errors if "email" in e.path]
        assert len(email_errors) > 0
        assert "Invalid email format" in email_errors[0].message

    def test_validate_email_format_missing_domain(self, temp_dir: Path):
        """Test email validation detects missing domain."""
        invalid_yaml = temp_dir / "no_domain.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": {"name": "Test", "email": "test@"}}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()

        email_errors = [e for e in validator.errors if "email" in e.path]
        assert len(email_errors) > 0


class TestPrintResults:
    """Test print_results method."""

    def test_print_results_success(self, sample_yaml_file: Path, capsys):
        """Test print_results for successful validation."""
        validator = ResumeValidator(sample_yaml_file)
        validator.validate_all()
        validator.print_results()

        captured = capsys.readouterr()
        assert "passed" in captured.out.lower()

    def test_print_results_with_warnings(self, sample_yaml_file: Path, capsys):
        """Test print_results with warnings."""
        validator = ResumeValidator(sample_yaml_file)
        # Manually add a warning
        validator.warnings.append(ValidationError("test", "Test warning", "warning"))
        validator.print_results()

        captured = capsys.readouterr()
        assert "warnings" in captured.out.lower()

    def test_print_results_with_errors(self, temp_dir: Path, capsys):
        """Test print_results with errors."""
        invalid_yaml = temp_dir / "invalid.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": "not a dict"}, f)

        validator = ResumeValidator(invalid_yaml)
        validator.validate_all()
        validator.print_results()

        captured = capsys.readouterr()
        assert "errors" in captured.out.lower()
        assert "failed" in captured.out.lower()


class TestValidateResumeFunction:
    """Test validate_resume function."""

    def test_validate_resume_valid(self, sample_yaml_file: Path):
        """Test validate_resume returns True for valid resume."""
        result = validate_resume(sample_yaml_file)
        assert result is True

    def test_validate_resume_invalid(self, temp_dir: Path, capsys):
        """Test validate_resume returns False for invalid resume."""
        invalid_yaml = temp_dir / "invalid.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"contact": "not a dict"}, f)

        result = validate_resume(invalid_yaml)

        assert result is False
        captured = capsys.readouterr()
        assert "errors" in captured.out.lower()
