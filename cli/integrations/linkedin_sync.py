"""LinkedIn integration for importing/exporting profile data."""

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
        Import LinkedIn profile data from JSON file.

        Args:
            json_path: Path to LinkedIn export JSON file

        Returns:
            Dictionary of profile data
        """
        if not json_path.exists():
            raise FileNotFoundError(f"LinkedIn data file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            linkedin_data = json.load(f)

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
            linkedin_data.get("profile", {}) or linkedin_data.get("Profile", {}) or linkedin_data
        )

        # Extract name
        first_name = (
            profile_data.get("firstName")
            or profile_data.get("first_name")
            or profile_data.get("FirstName")
        )
        last_name = (
            profile_data.get("lastName")
            or profile_data.get("last_name")
            or profile_data.get("LastName")
        )

        if first_name and last_name:
            contact["name"] = f"{first_name} {last_name}"
        elif profile_data.get("fullName") or profile_data.get("full_name"):
            contact["name"] = profile_data.get("fullName") or profile_data.get("full_name")

        # Extract email
        email = (
            profile_data.get("email")
            or profile_data.get("emailAddress")
            or profile_data.get("email_address")
        )
        if email:
            contact["email"] = email

        # Extract phone
        phone = (
            profile_data.get("phone")
            or profile_data.get("phoneNumber")
            or profile_data.get("phone_number")
        )
        if phone:
            contact["phone"] = phone

        # Extract location
        location = profile_data.get("location") or profile_data.get("Location", {})
        if isinstance(location, dict):
            city = location.get("city") or location.get("City")
            region = location.get("region") or location.get("Region")
            if city and region:
                contact["location"] = {"city": city, "state": region}
            elif city:
                contact["location"] = {"city": city}
        elif isinstance(location, str):
            contact["location"] = {"full": location}

        # Extract URLs
        urls = {}
        if profile_data.get("website") or profile_data.get("Website"):
            urls["website"] = profile_data.get("website") or profile_data.get("Website")
        if profile_data.get("linkedinUrl") or profile_data.get("linkedin_url"):
            urls["linkedin"] = profile_data.get("linkedinUrl") or profile_data.get("linkedin_url")
        if urls:
            contact["urls"] = urls

        return contact

    def _extract_summary(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract professional summary from LinkedIn data."""
        profile_data = (
            linkedin_data.get("profile", {}) or linkedin_data.get("Profile", {}) or linkedin_data
        )

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

        # Extract skill names
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

            company = exp.get("company") or exp.get("CompanyName") or exp.get("companyName") or ""

            title = exp.get("title") or exp.get("Title") or exp.get("jobTitle") or ""

            if not company or not title:
                continue

            # Parse dates
            start_date = self._parse_linkedin_date(exp.get("startDate") or exp.get("start_date"))
            end_date = self._parse_linkedin_date(exp.get("endDate") or exp.get("end_date"))

            # Location
            location = (
                exp.get("location") or exp.get("Location") or exp.get("companyLocation") or ""
            )

            # Description/bullets
            description = exp.get("description") or exp.get("Description") or ""

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

            institution = (
                edu.get("school")
                or edu.get("School")
                or edu.get("schoolName")
                or edu.get("institution")
                or ""
            )

            degree = edu.get("degree") or edu.get("Degree") or edu.get("degreeName") or ""

            if not institution:
                continue

            # Parse graduation date
            grad_date = self._parse_linkedin_date(
                edu.get("endDate") or edu.get("end_date") or edu.get("graduationYear")
            )

            # Location
            location = edu.get("schoolLocation") or edu.get("location") or ""

            # Field of study
            field = edu.get("fieldOfStudy") or edu.get("field_of_study") or edu.get("field") or ""

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

            name = cert.get("name") or cert.get("Name") or cert.get("certificationName") or ""

            if not name:
                continue

            # Issuing organization
            authority = (
                cert.get("authority")
                or cert.get("Authority")
                or cert.get("issuingOrganization")
                or ""
            )

            # Date
            date = self._parse_linkedin_date(
                cert.get("startDate") or cert.get("start_date") or cert.get("issueDate")
            )

            # URL
            url = cert.get("url") or cert.get("Url") or ""

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
