"""
Conversion utilities between resume-cli YAML format and JSON Resume standard format.

This module provides bidirectional conversion between:
- resume-cli YAML format (custom schema with variants)
- JSON Resume format (https://jsonresume.org/schema/)

The JSON Resume format is used by ResumeAI, allowing interoperability
between the two projects.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class JSONResumeConverter:
    """Converter between resume-cli YAML and JSON Resume formats."""

    # Mapping from resume-cli field names to JSON Resume field names
    # JSON Resume uses camelCase for most fields

    # Skill format compatibility
    # resume-cli can use either format:
    #   - Extended: {name: string, level: string, years: number, services: string[]}
    #   - Simple: string
    # JSON Resume uses: {name: string, keywords: string[]}

    @staticmethod
    def convert_skills_to_json_resume_format(skills: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert resume-cli skills to JSON Resume format.

        Supports both extended format ({name, level, years, services}) and simple format (string).

        Args:
            skills: Skills dictionary from resume-cli YAML

        Returns:
            List of skills in JSON Resume format
        """
        skill_list = []
        for category, skill_data in skills.items():
            if isinstance(skill_data, list):
                keywords = []
                for skill in skill_data:
                    if isinstance(skill, str):
                        keywords.append(skill)
                    elif isinstance(skill, dict):
                        # Extended format: extract name and optionally level/years/services
                        name = skill.get("name", "")
                        if name:
                            keywords.append(name)
                skill_list.append(
                    {
                        "name": category,
                        "keywords": keywords,
                    }
                )
            else:
                skill_list.append(
                    {
                        "name": category,
                        "keywords": [str(skill_data)] if skill_data else [],
                    }
                )
        return skill_list

    @staticmethod
    def convert_skills_to_extended_format(skills: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Convert JSON Resume skills format to resume-cli extended format.

        Args:
            skills: List of skills in JSON Resume format

        Returns:
            Dictionary with categories as keys and skill lists as values
        """
        skill_dict = {}
        for skill in skills:
            name = skill.get("name", "")
            keywords = skill.get("keywords", [])
            if name and keywords:
                # Convert simple keywords to extended format
                extended_skills = []
                for kw in keywords:
                    if isinstance(kw, str):
                        extended_skills.append({"name": kw})
                    else:
                        extended_skills.append(kw)
                skill_dict[name] = extended_skills
            elif name:
                skill_dict[name] = []
        return skill_dict

    @staticmethod
    def yaml_to_json_resume(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert resume-cli YAML format to JSON Resume format.

        Args:
            yaml_data: Resume data in resume-cli YAML format

        Returns:
            Resume data in JSON Resume format
        """
        json_resume: Dict[str, Any] = {}

        # Convert contact -> basics
        contact = yaml_data.get("contact", {})
        if contact:
            json_resume["basics"] = {
                "name": contact.get("name", ""),
                "label": contact.get("title", ""),  # Custom field
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "url": contact.get("urls", {}).get("website", ""),
                "summary": yaml_data.get("professional_summary", {}).get("base", ""),
                "location": JSONResumeConverter._convert_location(contact.get("location")),
                "profiles": JSONResumeConverter._convert_profiles(contact.get("urls", {})),
            }

        # Convert experience -> work
        experience = yaml_data.get("experience", [])
        if experience:
            json_resume["work"] = JSONResumeConverter._convert_experience(experience)

        # Convert education
        education = yaml_data.get("education", [])
        if education:
            json_resume["education"] = JSONResumeConverter._convert_education(education)

        # Convert skills
        skills = yaml_data.get("skills", {})
        if skills:
            json_resume["skills"] = JSONResumeConverter._convert_skills(skills)

        # Convert projects
        projects = yaml_data.get("projects", {})
        if projects:
            json_resume["projects"] = JSONResumeConverter._convert_projects(projects)

        # Convert publications
        publications = yaml_data.get("publications", [])
        if publications:
            json_resume["publications"] = JSONResumeConverter._convert_publications(publications)

        # Convert certifications
        certifications = yaml_data.get("certifications", [])
        if certifications:
            json_resume["certificates"] = JSONResumeConverter._convert_certifications(
                certifications
            )

        # Convert affiliations
        affiliations = yaml_data.get("affiliations", [])
        if affiliations:
            json_resume["references"] = JSONResumeConverter._convert_affiliations(affiliations)

        return json_resume

    @staticmethod
    def json_resume_to_yaml(
        json_data: Dict[str, Any], include_variants: bool = True
    ) -> Dict[str, Any]:
        """
        Convert JSON Resume format to resume-cli YAML format.

        Args:
            json_data: Resume data in JSON Resume format
            include_variants: Whether to include default variants configuration

        Returns:
            Resume data in resume-cli YAML format
        """
        yaml_data: Dict[str, Any] = {
            "meta": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
            }
        }

        # Convert basics -> contact
        basics = json_data.get("basics", {})
        if basics:
            urls = {}
            profiles = basics.get("profiles", [])
            if profiles:
                for profile in profiles:
                    network = profile.get("network", "").lower()
                    if network == "github":
                        urls["github"] = profile.get("url", "")
                    elif network == "linkedin":
                        urls["linkedin"] = profile.get("url", "")
                    elif network == "website":
                        urls["website"] = profile.get("url", "")

            location = basics.get("location", {})
            if location:
                location_str = ", ".join(
                    filter(
                        None,
                        [
                            location.get("city", ""),
                            location.get("region", ""),
                            location.get("countryCode", ""),
                        ],
                    )
                )

            yaml_data["contact"] = {
                "name": basics.get("name", ""),
                "title": basics.get("label", ""),
                "email": basics.get("email", ""),
                "phone": basics.get("phone", ""),
                "location": location_str if "location_str" in dir() else "",
                "urls": urls,
            }

            summary = basics.get("summary", "")
            if summary:
                yaml_data["professional_summary"] = {
                    "base": summary,
                }

        # Convert work -> experience
        work = json_data.get("work", [])
        if work:
            yaml_data["experience"] = JSONResumeConverter._convert_work_to_experience(work)

        # Convert education
        education = json_data.get("education", [])
        if education:
            yaml_data["education"] = JSONResumeConverter._convert_education_to_yaml(education)

        # Convert skills
        skills = json_data.get("skills", [])
        if skills:
            yaml_data["skills"] = JSONResumeConverter._convert_skills_to_yaml(skills)

        # Convert projects
        projects = json_data.get("projects", [])
        if projects:
            yaml_data["projects"] = JSONResumeConverter._convert_projects_to_yaml(projects)

        # Convert publications
        publications = json_data.get("publications", [])
        if publications:
            yaml_data["publications"] = JSONResumeConverter._convert_publications_to_yaml(
                publications
            )

        # Convert certificates
        certificates = json_data.get("certificates", [])
        if certificates:
            yaml_data["certifications"] = JSONResumeConverter._convert_certificates_to_yaml(
                certificates
            )

        # Add variants if requested
        if include_variants:
            yaml_data["variants"] = {
                "base": {
                    "description": "Standard resume variant",
                    "skill_sections": (
                        list(yaml_data.get("skills", {}).keys()) if "skills" in yaml_data else []
                    ),
                }
            }

        return yaml_data

    @staticmethod
    def _convert_location(location: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Convert location format."""
        if not location:
            return None
        return {
            "address": location.get("address", ""),
            "postalCode": location.get("postalCode", ""),
            "city": location.get("city", ""),
            "countryCode": location.get("countryCode", ""),
            "region": location.get("region", ""),
        }

    @staticmethod
    def _convert_profiles(urls: Optional[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert URLs to profiles format."""
        profiles = []
        if not urls:
            return profiles

        url_mapping = {
            "github": ("GitHub", "github"),
            "linkedin": ("LinkedIn", "linkedin"),
            "website": ("Website", "website"),
            "twitter": ("Twitter", "twitter"),
        }

        for key, (network, username) in url_mapping.items():
            if key in urls:
                profiles.append(
                    {
                        "network": network,
                        "username": username,
                        "url": urls[key],
                    }
                )

        return profiles

    @staticmethod
    def _convert_experience(experience: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert experience entries to work format."""
        work = []
        for job in experience:
            entry = {
                "company": job.get("company", ""),
                "position": job.get("title", ""),
                "startDate": job.get("start_date", ""),
                "endDate": job.get("end_date", ""),
                "summary": "",  # YAML doesn't have a summary field
                "highlights": JSONResumeConverter._convert_bullets_to_highlights(
                    job.get("bullets", [])
                ),
            }

            location = job.get("location")
            if location:
                entry["location"] = {"region": location}

            work.append(entry)

        return work

    @staticmethod
    def _convert_bullets_to_highlights(bullets: List[Union[str, Dict]]) -> List[str]:
        """Convert bullet points to highlights format."""
        highlights = []
        for bullet in bullets:
            if isinstance(bullet, str):
                highlights.append(bullet)
            elif isinstance(bullet, dict):
                highlights.append(bullet.get("text", ""))
        return highlights

    @staticmethod
    def _convert_education(education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert education entries."""
        edu = []
        for entry in education:
            edu_entry = {
                "institution": entry.get("institution", ""),
                "area": entry.get("field", ""),
                "studyType": entry.get("degree", ""),
                "startDate": entry.get("graduation_date", ""),
                "endDate": entry.get("graduation_date", ""),
            }

            location = entry.get("location")
            if location:
                edu_entry["location"] = {"region": location}

            courses = entry.get("courses", [])
            if courses:
                edu_entry["courses"] = courses

            edu.append(edu_entry)

        return edu

    @staticmethod
    def _convert_skills(skills: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert skills to JSON Resume format."""
        skill_list = []
        for category, skill_data in skills.items():
            if isinstance(skill_data, list):
                keywords = []
                for skill in skill_data:
                    if isinstance(skill, str):
                        keywords.append(skill)
                    elif isinstance(skill, dict):
                        keywords.append(skill.get("name", ""))
                skill_list.append(
                    {
                        "name": category,
                        "keywords": keywords,
                    }
                )
            else:
                skill_list.append(
                    {
                        "name": category,
                        "keywords": [str(skill_data)] if skill_data else [],
                    }
                )
        return skill_list

    @staticmethod
    def _convert_projects(projects: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert projects to JSON Resume format."""
        project_list = []
        for category, project_data in projects.items():
            if isinstance(project_data, list):
                for project in project_data:
                    if isinstance(project, dict):
                        project_entry = {
                            "name": project.get("name", category),
                            "description": project.get("description", ""),
                            "highlights": project.get("highlights", []),
                            "keywords": project.get("technologies", []),
                        }
                        if project.get("url"):
                            project_entry["url"] = project.get("url")
                        project_list.append(project_entry)
            elif isinstance(project_data, dict):
                project_entry = {
                    "name": project_data.get("name", category),
                    "description": project_data.get("description", ""),
                    "highlights": project_data.get("highlights", []),
                    "keywords": project_data.get("technologies", []),
                }
                if project_data.get("url"):
                    project_entry["url"] = project_data.get("url")
                project_list.append(project_entry)
        return project_list

    @staticmethod
    def _convert_publications(publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert publications to JSON Resume format."""
        pub_list = []
        for pub in publications:
            entry = {
                "name": pub.get("title", ""),
                "publisher": pub.get("journal", ""),
                "releaseDate": pub.get("year", ""),
                "url": pub.get("doi", ""),
            }
            if pub.get("authors"):
                entry["authors"] = [pub.get("authors")]
            pub_list.append(entry)
        return pub_list

    @staticmethod
    def _convert_certifications(certifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert certifications to JSON Resume format."""
        cert_list = []
        for cert in certifications:
            if isinstance(cert, dict):
                cert_list.append(
                    {
                        "name": cert.get("name", ""),
                        "date": cert.get("date", ""),
                        "issuer": cert.get("issuer", ""),
                    }
                )
            else:
                cert_list.append({"name": str(cert)})
        return cert_list

    @staticmethod
    def _convert_affiliations(affiliations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert affiliations to references format."""
        ref_list = []
        for aff in affiliations:
            if isinstance(aff, dict):
                ref_list.append(
                    {
                        "name": aff.get("name", ""),
                        "reference": aff.get("role", ""),
                    }
                )
        return ref_list

    # Methods for reverse conversion (JSON Resume -> YAML)

    @staticmethod
    def _convert_work_to_experience(work: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert work entries to experience format."""
        experience = []
        for job in work:
            bullets = []
            highlights = job.get("highlights", [])
            for highlight in highlights:
                bullets.append({"text": highlight})

            entry = {
                "company": job.get("company", ""),
                "title": job.get("position", ""),
                "start_date": job.get("startDate", ""),
                "end_date": job.get("endDate", ""),
                "bullets": bullets,
            }

            location = job.get("location", {})
            if location and location.get("region"):
                entry["location"] = location.get("region")

            experience.append(entry)

        return experience

    @staticmethod
    def _convert_education_to_yaml(education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert education entries to YAML format."""
        edu_list = []
        for edu in education:
            entry = {
                "institution": edu.get("institution", ""),
                "degree": edu.get("studyType", ""),
                "field": edu.get("area", ""),
                "graduation_date": edu.get("endDate", ""),
            }

            location = edu.get("location", {})
            if location:
                entry["location"] = location.get("region", "")

            courses = edu.get("courses", [])
            if courses:
                entry["courses"] = courses

            edu_list.append(entry)

        return edu_list

    @staticmethod
    def _convert_skills_to_yaml(skills: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Convert skills to YAML format."""
        skill_dict = {}
        for skill in skills:
            name = skill.get("name", "")
            keywords = skill.get("keywords", [])
            if name and keywords:
                skill_dict[name] = keywords
            elif name:
                skill_dict[name] = []
        return skill_dict

    @staticmethod
    def _convert_projects_to_yaml(
        projects: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Convert projects to YAML format."""
        project_dict = {}
        for project in projects:
            name = project.get("name", "Project")
            project_entry = {
                "name": name,
                "description": project.get("description", ""),
                "highlights": project.get("highlights", []),
            }
            keywords = project.get("keywords", [])
            if keywords:
                project_entry["technologies"] = keywords
            url = project.get("url")
            if url:
                project_entry["url"] = url

            project_dict[name] = [project_entry]

        return project_dict

    @staticmethod
    def _convert_publications_to_yaml(publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert publications to YAML format."""
        pub_list = []
        for pub in publications:
            entry = {
                "title": pub.get("name", ""),
                "year": pub.get("releaseDate", ""),
                "journal": pub.get("publisher", ""),
            }
            authors = pub.get("authors", [])
            if authors:
                entry["authors"] = authors[0] if len(authors) == 1 else ", ".join(authors)
            url = pub.get("url")
            if url:
                entry["doi"] = url
            pub_list.append(entry)
        return pub_list

    @staticmethod
    def _convert_certificates_to_yaml(certificates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert certificates to YAML format."""
        cert_list = []
        for cert in certificates:
            if isinstance(cert, dict):
                entry = {"name": cert.get("name", "")}
                if cert.get("date"):
                    entry["date"] = cert.get("date")
                if cert.get("issuer"):
                    entry["issuer"] = cert.get("issuer")
                cert_list.append(entry)
            else:
                cert_list.append({"name": str(cert)})
        return cert_list


def convert_yaml_to_json_resume(
    yaml_path: Union[str, Path], output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Convert resume-cli YAML file to JSON Resume format.

    Args:
        yaml_path: Path to resume.yaml file
        output_path: Optional path to save JSON output

    Returns:
        Dictionary in JSON Resume format
    """
    from .yaml_parser import ResumeYAML

    yaml_handler = ResumeYAML(Path(yaml_path))
    yaml_data = yaml_handler.load()

    json_resume = JSONResumeConverter.yaml_to_json_resume(yaml_data)

    if output_path:
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_resume, f, indent=2)

    return json_resume


def convert_json_resume_to_yaml(json_data: Dict[str, Any], output_path: Path) -> None:
    """
    Convert JSON Resume format to resume-cli YAML file.

    Args:
        json_data: Resume data in JSON Resume format
        output_path: Path to save YAML output
    """
    from .yaml_parser import ResumeYAML

    yaml_data = JSONResumeConverter.json_resume_to_yaml(json_data)

    yaml_handler = ResumeYAML(output_path)
    yaml_handler.save(yaml_data)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Convert between resume-cli YAML and JSON Resume formats"
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument("--to-json", action="store_true", help="Convert YAML to JSON Resume")
    parser.add_argument("--to-yaml", action="store_true", help="Convert JSON Resume to YAML")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if args.to_json:
        result = convert_yaml_to_json_resume(input_path, output_path)
        print(f"Converted to JSON Resume: {output_path}")
    elif args.to_yaml:
        with open(input_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        convert_json_resume_to_yaml(json_data, output_path)
        print(f"Converted to YAML: {output_path}")
    else:
        print("Please specify --to-json or --to-yaml")
