"""LinkedIn integration for importing/exporting profile data."""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class LinkedInSync:
    """Sync LinkedIn profile data to/from resume.yaml."""

    def __init__(self, config):
        """
        Initialize LinkedIn sync.

        Args:
            config: Config object
        """
        self.config = config
        self.linkedin_config = config.get("linkedin", {})

        # CSV field mapping from LinkedIn CSV export column names to internal keys
        self._csv_field_mapping = {
            "First Name": "firstName",
            "Last Name": "lastName",
            "Maiden Name": "maidenName",
            "Address": "address",
            "Birth Date": "birthDate",
            "Headline": "headline",
            "Summary": "summary",
            "Industry": "industry",
            "Zip Code": "zipCode",
            "Geo Location": "geoLocation",
            "Twitter Handles": "twitterHandles",
            "Websites": "websites",
            "Instant Messengers": "instantMessengers",
        }

    def import_from_url(self, url: str) -> Dict[str, Any]:
        """
        Parse LinkedIn profile from URL.

        Note: This method provides placeholder functionality.
        LinkedIn's API requires OAuth and restricted access.
        For production use, users should export their LinkedIn data
        and provide a JSON file instead.

        Args:
            url: LinkedIn profile URL

        Returns:
            Dictionary of profile data
        """
        raise NotImplementedError(
            "Direct LinkedIn URL import is not supported due to API restrictions.\n"
            "Please use --data-file option with exported LinkedIn JSON data.\n"
            "To export your LinkedIn data:\n"
            "1. Go to https://www.linkedin.com/psettings/member-data\n"
            "2. Request 'Profile' data export\n"
            "3. Use the downloaded JSON file with --data-file"
        )

    def import_from_json(self, json_path: Path) -> Dict[str, Any]:
        """
        Import LinkedIn profile data from JSON, CSV, or folder export.

        Automatically detects file format based on extension and content.
        Supports:
        - Single JSON file (LinkedIn JSON export)
        - Single CSV file (basic Profile.csv)
        - Folder with multiple CSV files (full LinkedIn data export)

        Args:
            json_path: Path to LinkedIn export file (JSON, CSV, or folder)

        Returns:
            Dictionary of profile data
        """
        if not json_path.exists():
            raise FileNotFoundError(f"LinkedIn data file not found: {json_path}")

        # Check if it's a directory (folder-based LinkedIn export)
        if json_path.is_dir():
            return self._import_from_folder(json_path)

        # Check file extension to determine format
        suffix = json_path.suffix.lower()

        if suffix == ".csv":
            return self._import_from_csv(json_path)
        elif suffix == ".json":
            return self._import_from_json_file(json_path)
        else:
            # Try to detect format by reading first character
            return self._import_from_json_file(json_path)

    def _import_from_folder(self, folder_path: Path) -> Dict[str, Any]:
        """
        Import LinkedIn profile data from a folder export.

        Handles LinkedIn's full data export folder containing multiple CSV files.

        Args:
            folder_path: Path to LinkedIn export folder

        Returns:
            Dictionary of profile data
        """
        linkedin_data = {}

        # Define the expected CSV files and their data keys
        csv_mappings = {
            "Profile.csv": "profile",
            "Positions.csv": "positions",
            "Education.csv": "education",
            "Skills.csv": "skills",
            "Certifications.csv": "certifications",
        }

        for csv_file, data_key in csv_mappings.items():
            csv_path = folder_path / csv_file
            if csv_path.exists():
                try:
                    data = self._read_csv_file(csv_path, csv_file)
                    if data:
                        linkedin_data[data_key] = data
                except Exception as e:
                    # Log but continue - some files may be missing or malformed
                    import logging
                    logging.warning(f"Error reading {csv_file}: {e}")

        # Also check for Profile Summary.csv
        profile_summary_path = folder_path / "Profile Summary.csv"
        if profile_summary_path.exists():
            try:
                summary_data = self._read_csv_file(profile_summary_path, "Profile Summary.csv")
                if summary_data and len(summary_data) > 0:
                    # The Profile Summary CSV typically has 'Summary' column
                    row = summary_data[0]
                    if "Summary" in row and row["Summary"]:
                        linkedin_data["profile"]["summary"] = row["Summary"]
            except Exception:
                pass

        # Map LinkedIn data to resume.yaml structure
        resume_data = self._map_linkedin_to_resume(linkedin_data)

        return resume_data

    def _read_csv_file(self, csv_path: Path, file_name: str) -> List[Dict[str, Any]]:
        """
        Read a CSV file and return list of dictionaries.

        Args:
            csv_path: Path to CSV file
            file_name: Name of file for field mapping

        Returns:
            List of row dictionaries
        """
        rows = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up empty values
                cleaned_row = {k: v.strip() if v else "" for k, v in row.items()}
                rows.append(cleaned_row)
        return rows

    def _import_from_json_file(self, json_path: Path) -> Dict[str, Any]:
        """
        Import LinkedIn profile data from JSON file.

        Args:
            json_path: Path to LinkedIn export JSON file

        Returns:
            Dictionary of profile data
        """
        try:
            with open(json_path, encoding="utf-8") as f:
                linkedin_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON file: {json_path}. "
                f"The file appears to be in CSV format. "
                f"Please use a LinkedIn JSON export or convert your CSV to JSON.\n"
                f"JSON error: {e}"
            ) from e

        # Map LinkedIn data to resume.yaml structure
        resume_data = self._map_linkedin_to_resume(linkedin_data)

        return resume_data

    def _import_from_csv(self, csv_path: Path) -> Dict[str, Any]:
        """
        Import LinkedIn profile data from CSV file.

        Handles LinkedIn's basic CSV profile export format.

        Args:
            csv_path: Path to LinkedIn CSV export file

        Returns:
            Dictionary of profile data
        """
        linkedin_data = {}

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if not rows:
                raise ValueError(f"CSV file is empty: {csv_path}")

            # Get the first (and usually only) row for profile data
            row = rows[0]

            # Map CSV columns to internal format using the field mapping
            for csv_field, internal_key in self._csv_field_mapping.items():
                if csv_field in row and row[csv_field]:
                    linkedin_data[internal_key] = row[csv_field]

            # Handle positions/experience if present in CSV
            # (Basic CSV export may not have this, but check for additional rows)
            if len(rows) > 1:
                positions = []
                for row in rows[1:]:
                    # Check if this row has position data
                    if row.get("Company") or row.get("Title"):
                        position = {
                            "company": row.get("Company", ""),
                            "title": row.get("Title", ""),
                            "location": row.get("Location", ""),
                            "startDate": row.get("Start Date", ""),
                            "endDate": row.get("End Date", ""),
                            "description": row.get("Description", ""),
                        }
                        positions.append(position)
                if positions:
                    linkedin_data["positions"] = positions

        # Map LinkedIn data to resume.yaml structure
        resume_data = self._map_linkedin_to_resume(linkedin_data)

        return resume_data

    def _map_linkedin_to_resume(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map LinkedIn profile data to resume.yaml structure.

        Args:
            linkedin_data: Parsed LinkedIn export data

        Returns:
            Dictionary matching resume.yaml schema
        """
        resume_data = {
            "meta": {
                "version": "2.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "source": "linkedin_import",
            },
            "contact": self._extract_contact(linkedin_data),
            "professional_summary": self._extract_summary(linkedin_data),
            "skills": self._extract_skills(linkedin_data),
            "experience": self._extract_experience(linkedin_data),
            "education": self._extract_education(linkedin_data),
            "certifications": self._extract_certifications(linkedin_data),
            "projects": {},
            "variants": {},
        }

        return resume_data

    def _extract_contact(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information from LinkedIn data."""
        contact = {}

        # LinkedIn export data structure varies by export format
        # Try multiple common paths
        profile_data = (
            linkedin_data.get("profile", []) or linkedin_data.get("Profile", {}) or linkedin_data
        )

        # Handle list format from CSV (folder export)
        if isinstance(profile_data, list) and len(profile_data) > 0:
            profile_data = profile_data[0]

        # Extract name - handle CSV format with "First Name" and "Last Name"
        first_name = (
            profile_data.get("firstName")
            or profile_data.get("first_name")
            or profile_data.get("FirstName")
            or profile_data.get("First Name")
        )
        last_name = (
            profile_data.get("lastName")
            or profile_data.get("last_name")
            or profile_data.get("LastName")
            or profile_data.get("Last Name")
        )

        if first_name and last_name:
            contact["name"] = f"{first_name} {last_name}"
        elif profile_data.get("fullName") or profile_data.get("full_name"):
            contact["name"] = profile_data.get("fullName") or profile_data.get("full_name")

        # Extract headline (for profile display)
        headline = (
            profile_data.get("headline")
            or profile_data.get("Headline")
            or profile_data.get("Headline")
        )
        if headline:
            contact["headline"] = headline

        # Extract location - handle CSV format with "Geo Location"
        location = (
            profile_data.get("location")
            or profile_data.get("Location")
            or profile_data.get("geoLocation")
            or profile_data.get("Geo Location")
        )
        if location:
            contact["location"] = {"full": location}

        # Extract URLs from Websites field (CSV format)
        websites = profile_data.get("websites") or profile_data.get("Websites") or ""
        if websites:
            urls = {}
            # Parse website URLs (may be comma-separated)
            if isinstance(websites, str):
                website_list = [w.strip() for w in websites.split(",") if w.strip()]
                for i, url in enumerate(website_list[:3]):  # Limit to 3 URLs
                    if i == 0:
                        urls["website"] = url
                    else:
                        urls[f"website_{i+1}"] = url
            if urls:
                contact["urls"] = urls

        # Extract industry (for reference)
        industry = profile_data.get("industry") or profile_data.get("Industry")
        if industry:
            contact["industry"] = industry

        return contact

    def _extract_summary(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract professional summary from LinkedIn data."""
        profile_data = (
            linkedin_data.get("profile", {}) or linkedin_data.get("Profile", {}) or linkedin_data
        )

        # Handle list format from CSV (folder export)
        if isinstance(profile_data, list) and len(profile_data) > 0:
            profile_data = profile_data[0]

        summary = (
            profile_data.get("summary")
            or profile_data.get("Summary")
            or profile_data.get("headline")
            or profile_data.get("Headline")
            or ""
        )

        return {"base": summary, "variants": {}}

    def _extract_skills(self, linkedin_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract skills from LinkedIn data."""
        skills_data = linkedin_data.get("skills") or linkedin_data.get("Skills") or []

        if not isinstance(skills_data, list):
            # Try nested structure
            skills_data = []

        # Extract skill names - handle CSV format with "Name" column
        skill_names = []
        for skill in skills_data:
            if isinstance(skill, dict):
                name = (
                    skill.get("name")
                    or skill.get("Name")
                    or skill.get("skillName")
                    or skill.get("skillName")
                )
            elif isinstance(skill, str):
                name = skill
            else:
                continue

            if name:
                skill_names.append(name)

        # Categorize skills (simple keyword-based categorization)
        categorized = self._categorize_skills(skill_names)

        return categorized

    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize skills based on keywords.

        Args:
            skills: List of skill names

        Returns:
            Dictionary of categorized skills
        """
        categories = {
            "languages": [],
            "frameworks": [],
            "tools": [],
            "cloud_platforms": [],
            "databases": [],
            "other": [],
        }

        language_keywords = [
            "python",
            "javascript",
            "java",
            "go",
            "rust",
            "c\\+\\+",
            "c#",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "haskell",
            "typescript",
            "sql",
        ]

        framework_keywords = [
            "django",
            "flask",
            "fastapi",
            "spring",
            "react",
            "angular",
            "vue",
            "express",
            "rails",
            "laravel",
            "next\\.js",
            "nuxt",
            "tensorflow",
            "pytorch",
            "keras",
            "pandas",
            "numpy",
            "scikit",
            "langchain",
        ]

        cloud_keywords = [
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "amazon web services",
            "heroku",
            "vercel",
            "netlify",
            "digitalocean",
            "linode",
        ]

        database_keywords = [
            "postgres",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "sqlite",
            "oracle",
            "sql server",
            "cassandra",
            "elasticsearch",
            "dynamodb",
        ]

        tool_keywords = [
            "docker",
            "kubernetes",
            "git",
            "github",
            "gitlab",
            "jenkins",
            "circleci",
            "terraform",
            "ansible",
            "nagios",
            "grafana",
            "prometheus",
        ]

        for skill in skills:
            skill_lower = skill.lower()

            # Check each category (use first match)
            matched = False
            patterns = [
                (language_keywords, "languages"),
                (framework_keywords, "frameworks"),
                (cloud_keywords, "cloud_platforms"),
                (database_keywords, "databases"),
                (tool_keywords, "tools"),
            ]

            for keywords, category in patterns:
                if any(re.search(rf"\b{kw}\b", skill_lower) for kw in keywords):
                    categories[category].append(skill)
                    matched = True
                    break

            if not matched:
                categories["other"].append(skill)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _extract_experience(self, linkedin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract work experience from LinkedIn data."""
        experience_data = (
            linkedin_data.get("experience")
            or linkedin_data.get("Experience")
            or linkedin_data.get("positions")
            or linkedin_data.get("Positions")
            or []
        )

        if not isinstance(experience_data, list):
            return []

        experience = []
        for exp in experience_data:
            if not isinstance(exp, dict):
                continue

            # Handle different CSV column names from folder export
            # CSV format: "Company Name", "Title", "Description", "Location", "Started On", "Finished On"
            company = (
                exp.get("company")
                or exp.get("CompanyName")
                or exp.get("companyName")
                or exp.get("Company Name")
                or ""
            )

            title = (
                exp.get("title")
                or exp.get("Title")
                or exp.get("jobTitle")
                or exp.get("Job Title")
                or ""
            )

            if not company or not title:
                continue

            # Parse dates - handle CSV format "Started On", "Finished On"
            start_date = self._parse_linkedin_date(
                exp.get("startDate")
                or exp.get("start_date")
                or exp.get("Started On")
                or exp.get("start_date")
            )
            end_date = self._parse_linkedin_date(
                exp.get("endDate")
                or exp.get("end_date")
                or exp.get("Finished On")
                or exp.get("end_date")
            )

            # Handle empty end date (current position)
            if end_date == "" or end_date is None:
                end_date = "Present"

            # Location - handle CSV format
            location = (
                exp.get("location")
                or exp.get("Location")
                or exp.get("companyLocation")
                or exp.get("Company Location")
                or ""
            )

            # Description/bullets - handle CSV format
            description = (
                exp.get("description")
                or exp.get("Description")
                or exp.get("Description")
                or ""
            )

            bullets = self._parse_description_to_bullets(description)

            experience_entry = {
                "company": company,
                "title": title,
                "start_date": start_date,
                "end_date": end_date,
                "location": location,
                "bullets": bullets,
            }

            experience.append(experience_entry)

        # Sort by start date (most recent first)
        experience.sort(
            key=lambda x: (x["start_date"] or "1900-01", x["end_date"] or "9999-12"), reverse=True
        )

        return experience

    def _parse_linkedin_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse LinkedIn date to YYYY-MM format.

        Args:
            date_str: Date string from LinkedIn (various formats)

        Returns:
            Date in YYYY-MM format or None
        """
        if not date_str:
            return None

        # Common LinkedIn date formats
        formats = ["%Y-%m-%d", "%Y-%m", "%B %Y", "%b %Y", "%Y", "%m/%Y", "%m/%d/%Y"]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m")
            except ValueError:
                continue

        # Try extracting year from string
        year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
        if year_match:
            return f"{year_match.group()}-01"

        return None

    def _parse_description_to_bullets(self, description: str) -> List[Dict[str, Any]]:
        """
        Parse job description into bullet points.

        Args:
            description: Job description text

        Returns:
            List of bullet dictionaries
        """
        if not description:
            return []

        # Split by common bullet indicators
        bullet_pattern = r"[\n•\-\*]+\s*"
        raw_bullets = re.split(bullet_pattern, description)

        bullets = []
        for text in raw_bullets:
            text = text.strip()
            if len(text) > 10:  # Ignore very short bullets
                bullets.append({"text": text, "skills": [], "emphasize_for": []})

        # If no bullets found, treat whole description as one bullet
        if not bullets and len(description) > 20:
            bullets.append({"text": description, "skills": [], "emphasize_for": []})

        return bullets

    def _extract_education(self, linkedin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract education from LinkedIn data."""
        education_data = linkedin_data.get("education") or linkedin_data.get("Education") or []

        if not isinstance(education_data, list):
            return []

        education = []
        for edu in education_data:
            if not isinstance(edu, dict):
                continue

            # Handle CSV column names from folder export
            # CSV format: "School Name", "Start Date", "End Date", "Notes", "Degree Name", "Activities"
            institution = (
                edu.get("school")
                or edu.get("School")
                or edu.get("schoolName")
                or edu.get("institution")
                or edu.get("School Name")
                or ""
            )

            degree = (
                edu.get("degree")
                or edu.get("Degree")
                or edu.get("degreeName")
                or edu.get("Degree Name")
                or ""
            )

            if not institution:
                continue

            # Parse graduation date - handle CSV format "End Date"
            grad_date = self._parse_linkedin_date(
                edu.get("endDate")
                or edu.get("end_date")
                or edu.get("graduationYear")
                or edu.get("End Date")
            )

            # Location (not typically in CSV, but handle anyway)
            location = edu.get("schoolLocation") or edu.get("location") or edu.get("Location") or ""

            # Field of study - handle CSV "Notes" column sometimes contains field info
            field = (
                edu.get("fieldOfStudy")
                or edu.get("field_of_study")
                or edu.get("field")
                or edu.get("Field of Study")
                or ""
            )

            # If field is empty but Notes contains info, use Notes for field
            if not field and edu.get("Notes"):
                field = edu.get("Notes")

            education_entry = {
                "institution": institution,
                "degree": degree,
                "graduation_date": grad_date or "",
                "location": location,
                "field": field,
            }

            education.append(education_entry)

        # Sort by graduation date (most recent first)
        education.sort(key=lambda x: (x["graduation_date"] or "1900-01"), reverse=True)

        return education

    def _extract_certifications(self, linkedin_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract certifications from LinkedIn data."""
        cert_data = (
            linkedin_data.get("certifications")
            or linkedin_data.get("Certifications")
            or linkedin_data.get("certifications")
            or []
        )

        if not isinstance(cert_data, list):
            return []

        certifications = []
        for cert in cert_data:
            if not isinstance(cert, dict):
                continue

            # Handle CSV column names from folder export
            # CSV format: "Name", "Url", "Authority", "Started On", "Finished On", "License Number"
            name = (
                cert.get("name")
                or cert.get("Name")
                or cert.get("certificationName")
                or cert.get("Certification Name")
                or ""
            )

            if not name:
                continue

            # Issuing organization - handle CSV "Authority" column
            authority = (
                cert.get("authority")
                or cert.get("Authority")
                or cert.get("issuingOrganization")
                or cert.get("Issuer")
                or ""
            )

            # Date - handle CSV "Started On" and "Finished On" columns
            date = self._parse_linkedin_date(
                cert.get("startDate")
                or cert.get("start_date")
                or cert.get("issueDate")
                or cert.get("Started On")
                or cert.get("Finished On")
            )

            # URL
            url = cert.get("url") or cert.get("Url") or cert.get("URL") or ""

            # License number (may be useful)
            license_num = cert.get("License Number") or cert.get("licenseNumber") or ""

            certifications.append(
                {"name": name, "issuer": authority, "date": date or "", "url": url}
            )

        return certifications

    def export_to_linkedin_format(self, yaml_path: Path, output_path: Optional[Path] = None) -> str:
        """
        Export resume.yaml data to LinkedIn-friendly format.

        Args:
            yaml_path: Path to resume.yaml
            output_path: Optional output file path

        Returns:
            LinkedIn-formatted text
        """
        from ..utils.yaml_parser import ResumeYAML

        yaml_handler = ResumeYAML(yaml_path)
        data = yaml_handler.load()

        # Build LinkedIn-formatted content
        sections = []

        # Headline (Professional Summary)
        summary = data.get("professional_summary", {}).get("base", "")
        if summary:
            sections.append(f"Headline:\n{summary}\n")

        # Experience
        experience = data.get("experience", [])
        if experience:
            sections.append("\nExperience:")
            for exp in experience:
                sections.append(f"\n{exp.get('title', '')} | {exp.get('company', '')}")
                if exp.get("location"):
                    sections.append(f"Location: {exp['location']}")

                # Format dates
                start = exp.get("start_date", "")
                end = exp.get("end_date") or "Present"
                if start:
                    sections.append(f"{self._format_date_range(start, end)}")

                # Bullets
                bullets = exp.get("bullets", [])
                for bullet in bullets:
                    if isinstance(bullet, dict):
                        text = bullet.get("text", "")
                    else:
                        text = str(bullet)
                    if text:
                        sections.append(f"• {text}")

        # Skills
        skills = data.get("skills", {})
        if skills:
            sections.append("\n\nSkills:")
            for category, skill_list in skills.items():
                if skill_list:
                    skill_names = []
                    for s in skill_list:
                        skill_names.append(s if isinstance(s, str) else s.get("name", ""))
                    sections.append(f"{category.title()}: {', '.join(skill_names)}")

        # Education
        education = data.get("education", [])
        if education:
            sections.append("\n\nEducation:")
            for edu in education:
                sections.append(f"\n{edu.get('institution', '')}")
                if edu.get("degree"):
                    sections.append(f"{edu.get('degree', '')}")
                if edu.get("field"):
                    sections.append(f"Field: {edu['field']}")
                if edu.get("graduation_date"):
                    sections.append(f"Graduated: {edu['graduation_date']}")

        # Certifications
        certifications = data.get("certifications", [])
        if certifications:
            sections.append("\n\nCertifications:")
            for cert in certifications:
                name = cert.get("name", "")
                issuer = cert.get("issuer", "")
                date = cert.get("date", "")
                cert_line = f"• {name}"
                if issuer:
                    cert_line += f" - {issuer}"
                if date:
                    cert_line += f" ({date})"
                sections.append(cert_line)

        linkedin_content = "\n".join(sections)

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(linkedin_content)

        return linkedin_content

    def _format_date_range(self, start: str, end: str) -> str:
        """
        Format date range for LinkedIn.

        Args:
            start: Start date (YYYY-MM)
            end: End date (YYYY-MM or "Present")

        Returns:
            Formatted date range
        """
        # Convert YYYY-MM to month year format
        try:
            start_dt = datetime.strptime(start, "%Y-%m")
            start_formatted = start_dt.strftime("%b %Y")
        except ValueError:
            start_formatted = start

        if end == "Present" or not end:
            end_formatted = "Present"
        else:
            try:
                end_dt = datetime.strptime(end, "%Y-%m")
                end_formatted = end_dt.strftime("%b %Y")
            except ValueError:
                end_formatted = end

        return f"{start_formatted} - {end_formatted}"
