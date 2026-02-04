"""Initialize resume.yaml from existing resume files."""

import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def init_from_existing(
    base_resume_path: Optional[Path] = None,
    revised_resume_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Initialize resume.yaml by parsing existing resume files.

    Args:
        base_resume_path: Path to base_resume.txt or similar
        revised_resume_path: Path to REVISED.md or similar
        output_path: Where to save resume.yaml

    Returns:
        Path to created resume.yaml
    """
    if output_path is None:
        output_path = Path.cwd() / "resume.yaml"

    # Default paths
    job_hunt_dir = Path(__file__).parent.parent.parent

    if base_resume_path is None:
        base_resume_path = job_hunt_dir / "resumes" / "base_resume.txt"

    if revised_resume_path is None:
        revised_resume_path = job_hunt_dir / "Alex Chapin - Resume - REVISED.md"

    # Parse resumes
    data = {
        "meta": {
            "version": "2.0.0",
            "last_updated": "",
            "author": "Alex Chapin"
        },
        "contact": {},
        "professional_summary": {"base": "", "variants": {}},
        "skills": {},
        "experience": [],
        "education": [],
        "publications": [],
        "certifications": [],
        "affiliations": [],
        "projects": {},
        "variants": {}
    }

    # Parse base resume
    if base_resume_path and base_resume_path.exists():
        print(f"Parsing {base_resume_path}...")
        _parse_base_resume(base_resume_path, data)

    # Parse revised resume for additional info
    if revised_resume_path and revised_resume_path.exists():
        print(f"Parsing {revised_resume_path}...")
        _parse_revised_resume(revised_resume_path, data)

    # Add variants
    _add_default_variants(data)

    # Write YAML
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\n✓ Created {output_path}")
    print("  Please review and update the file as needed.")

    return output_path


def _parse_base_resume(path: Path, data: Dict[str, Any]) -> None:
    """Parse base_resume.txt format."""
    content = path.read_text()

    # Parse contact info (first few lines)
    lines = content.split("\n")

    # Name and credentials (line 1)
    match = re.match(r"^(.+?)(?:,\s*(P\.E\.|PhD))?$", lines[0])
    if match:
        data["contact"]["name"] = match.group(1).strip()
        if match.group(2):
            data["contact"]["credentials"] = [match.group(2)]

    # Phone and email (line 2)
    if len(lines) > 1:
        contact_match = re.search(r"([\d-]+)\s*\|\s*(.+)", lines[1])
        if contact_match:
            data["contact"]["phone"] = contact_match.group(1).strip()
            data["contact"]["email"] = contact_match.group(2).strip()

    # Parse sections
    current_section = None
    current_job = None

    for line in lines[2:]:
        line = line.strip()

        # Section headers
        if line.upper() == "PROFESSIONAL SUMMARY":
            current_section = "summary"
            continue
        elif line.upper() == "TECHNICAL SKILLS":
            current_section = "skills"
            continue
        elif line.upper() == "EXPERIENCE":
            current_section = "experience"
            continue
        elif line.upper() == "EDUCATION":
            current_section = "education"
            continue
        elif line.upper() == "PUBLICATIONS & LICENSES":
            current_section = "publications"
            continue
        elif line == "" or line == "---":
            continue

        # Parse content based on section
        if current_section == "summary" and line:
            data["professional_summary"]["base"] = line

        elif current_section == "skills" and line.startswith("•"):
            skill_text = line[1:].strip()
            # Parse skill category
            if ":" in skill_text:
                category, skills = skill_text.split(":", 1)
                category = category.strip().lower().replace(" ", "_").replace("&", "and")
                skills_list = [s.strip() for s in skills.split(",")]
                data["skills"][category] = skills_list

        elif current_section == "experience":
            # Job header: "Company | Year – Year"
            job_match = re.match(r"^(.+?)\s*\|\s*(\d+)\s*–\s*(Present|\d+)", line)
            if job_match:
                current_job = {
                    "company": job_match.group(1).strip(),
                    "start_date": f"{job_match.group(2)}-01",
                    "end_date": None if job_match.group(3) == "Present" else f"{job_match.group(3)}-01",
                    "bullets": []
                }
                data["experience"].append(current_job)
            elif line.startswith("•") and current_job:
                bullet_text = line[1:].strip()
                # Extract label if present
                label_match = re.match(r"^([^:]+):\s*(.+)$", bullet_text)
                if label_match:
                    label = label_match.group(1).strip()
                    text = label_match.group(2).strip()
                    current_job["bullets"].append({
                        "text": text,
                        "skills": [label.replace(":", "").strip()]
                    })
                else:
                    current_job["bullets"].append({"text": bullet_text})

        elif current_section == "education":
            # Education: "Degree | Institution | Year"
            edu_match = re.match(r"^(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)", line)
            if edu_match:
                data["education"].append({
                    "degree": edu_match.group(1).strip(),
                    "institution": edu_match.group(2).strip(),
                    "graduation_date": f"{edu_match.group(3)}-01"
                })

        elif current_section == "publications" and line.startswith("•"):
            pub_text = line[1:].strip()
            if "Publication:" in pub_text:
                pub_text = pub_text.replace("Publication:", "").strip()
            data["publications"].append({"title": pub_text})

        elif current_section == "publications" and line.startswith("•") and "License:" in line:
            data["certifications"].append({
                "name": "Licensed Professional Engineer",
                "license_number": "58110"
            })


def _parse_revised_resume(path: Path, data: Dict[str, Any]) -> None:
    """Parse REVISED.md for additional details."""
    content = path.read_text()

    # Extract location
    location_match = re.search(r"(.+?),\s*([A-Z]{2})\s*(\d+)", content)
    if location_match:
        data["contact"]["location"] = {
            "city": location_match.group(1).strip(),
            "state": location_match.group(2).strip(),
            "zip": location_match.group(3).strip()
        }

    # Extract URLs
    github_match = re.search(r"github\.com/([\w-]+)", content)
    if github_match:
        data["contact"]["urls"] = data["contact"].get("urls", {})
        data["contact"]["urls"]["github"] = f"https://github.com/{github_match.group(1)}"

    linkedin_match = re.search(r"linkedin\.com/in/([\w-]+)", content)
    if linkedin_match:
        data["contact"]["urls"] = data["contact"].get("urls", {})
        data["contact"]["urls"]["linkedin"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"


def _add_default_variants(data: Dict[str, Any]) -> None:
    """Add default variant configurations."""
    data["variants"] = {
        "v1.0.0-base": {
            "description": "General software engineering",
            "summary_key": "base",
            "skill_sections": list(data["skills"].keys()) if data["skills"] else [],
            "max_bullets_per_job": 4,
            "emphasize_keywords": []
        },
        "v1.1.0-backend": {
            "description": "Backend & DevOps specialization",
            "summary_key": "base",
            "skill_sections": ["programming_languages", "cloud_devops", "databases"],
            "max_bullets_per_job": 5,
            "emphasize_keywords": ["backend", "api", "scalability"]
        },
        "v1.2.0-ml_ai": {
            "description": "ML/AI specialization",
            "summary_key": "base",
            "skill_sections": ["programming_languages", "ai_ml"],
            "max_bullets_per_job": 5,
            "emphasize_keywords": ["ai", "ml", "machine learning", "llm"]
        },
        "v1.3.0-fullstack": {
            "description": "Full-stack specialization",
            "summary_key": "base",
            "skill_sections": ["programming_languages", "frontend", "backend"],
            "max_bullets_per_job": 4,
            "emphasize_keywords": ["fullstack", "react", "web"]
        }
    }


if __name__ == "__main__":
    import sys
    output = init_from_existing()
    sys.exit(0)
