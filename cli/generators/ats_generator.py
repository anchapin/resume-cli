"""ATS (Applicant Tracking System) score checker."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..utils.config import Config
from ..utils.yaml_parser import ResumeYAML

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

console = Console()


@dataclass
class ATSCategoryScore:
    """Score for a single ATS category."""

    name: str
    points_earned: int
    points_possible: int
    details: List[str]
    suggestions: List[str]

    @property
    def percentage(self) -> float:
        """Calculate percentage score."""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100


@dataclass
class ATSReport:
    """Complete ATS score report."""

    total_score: int
    total_possible: int
    categories: Dict[str, ATSCategoryScore]
    summary: str
    recommendations: List[str]

    @property
    def overall_percentage(self) -> float:
        """Calculate overall percentage."""
        if self.total_possible == 0:
            return 0.0
        return (self.total_score / self.total_possible) * 100


class ATSGenerator:
    """Generate ATS scores and reports for resumes."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize ATS generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.yaml_handler = ResumeYAML(yaml_path)

        # Initialize AI client (optional - will use fallback methods if not available)
        self.client = None
        self.provider = None
        self.ai_available = False

        try:
            provider = self.config.ai_provider

            if provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    console.print("[dim]AI not available - using fallback keyword extraction[/dim]")
                else:
                    import os

                    api_key = os.getenv("ANTHROPIC_API_KEY")
                    if api_key:
                        base_url = os.getenv("ANTHROPIC_BASE_URL") or self.config.anthropic_base_url
                        client_kwargs = {"api_key": api_key}
                        if base_url:
                            client_kwargs["base_url"] = base_url
                        self.client = anthropic.Anthropic(**client_kwargs)
                        self.provider = "anthropic"
                        self.ai_available = True
                    else:
                        console.print(
                            "[dim]ANTHROPIC_API_KEY not set - using fallback keyword extraction[/dim]"
                        )

            elif provider == "openai":
                if not OPENAI_AVAILABLE:
                    console.print("[dim]AI not available - using fallback keyword extraction[/dim]")
                else:
                    import os

                    api_key = os.getenv("OPENAI_API_KEY")
                    if api_key:
                        base_url = os.getenv("OPENAI_BASE_URL") or self.config.openai_base_url
                        client_kwargs = {"api_key": api_key}
                        if base_url:
                            client_kwargs["base_url"] = base_url
                        self.client = openai.OpenAI(**client_kwargs)
                        self.provider = "openai"
                        self.ai_available = True
                    else:
                        console.print(
                            "[dim]OPENAI_API_KEY not set - using fallback keyword extraction[/dim]"
                        )

        except Exception as e:
            console.print(f"[dim]AI initialization failed ({e}) - using fallback methods[/dim]")

    def generate_report(self, job_description: str, variant: Optional[str] = None) -> ATSReport:
        """
        Generate comprehensive ATS report.

        Args:
            job_description: Job description text
            variant: Resume variant to check (optional)

        Returns:
            ATSReport object with scores and recommendations
        """
        # Get resume data
        resume_data = self._get_resume_data(variant)

        # Calculate scores for each category
        categories = {
            "format_parsing": self._check_format_parsing(resume_data),
            "keywords": self._check_keywords(resume_data, job_description),
            "section_structure": self._check_section_structure(resume_data),
            "contact_info": self._check_contact_info(resume_data),
            "readability": self._check_readability(resume_data),
        }

        # Calculate total score
        total_score = sum(cat.points_earned for cat in categories.values())
        total_possible = sum(cat.points_possible for cat in categories.values())

        # Generate summary and recommendations
        summary, recommendations = self._generate_summary(categories, total_score, total_possible)

        return ATSReport(
            total_score=total_score,
            total_possible=total_possible,
            categories=categories,
            summary=summary,
            recommendations=recommendations,
        )

    def _get_resume_data(self, variant: Optional[str]) -> Dict[str, Any]:
        """Get resume data for variant."""
        return {
            "contact": self.yaml_handler.get_contact(),
            "summary": self.yaml_handler.get_summary(variant),
            "skills": self.yaml_handler.get_skills(variant),
            "experience": self.yaml_handler.get_experience(variant),
            "education": self.yaml_handler.get_education(variant),
            "projects": self.yaml_handler.get_projects(variant),
        }

    def _check_format_parsing(self, resume_data: Dict[str, Any]) -> ATSCategoryScore:
        """
        Check if resume format is ATS-friendly.

        Score: 20 points
        """
        points = 20
        details = []
        suggestions = []

        # Check if data is structured (not images)
        if resume_data.get("contact"):
            details.append("Structured text format (no images)")
        else:
            points -= 20
            suggestions.append("Convert to text-only format (no images/tables)")

        # Check for complex formatting indicators
        all_text = self._get_all_text(resume_data)
        has_tables = bool(re.search(r"\|[^\n]+\|", all_text))
        has_special_chars = len(re.findall(r"[^a-zA-Z0-9\s\-\.\,\@\(\)\#\/]", all_text))

        if not has_tables:
            details.append("No tables detected (ATS-friendly)")
        else:
            points -= 10
            details.append("Tables detected (may cause parsing issues)")
            suggestions.append("Remove tables or convert to simple lists")

        if has_special_chars < 50:
            details.append("Minimal special characters (good)")
        else:
            points -= 5
            suggestions.append("Reduce special characters for better parsing")

        return ATSCategoryScore(
            name="Format Parsing",
            points_earned=max(0, points),
            points_possible=20,
            details=details,
            suggestions=suggestions,
        )

    def _check_keywords(
        self, resume_data: Dict[str, Any], job_description: str
    ) -> ATSCategoryScore:
        """
        Check keyword matching between resume and job description.

        Score: 30 points
        Uses AI to extract and compare keywords.
        """
        points = 30
        details = []
        suggestions = []

        # Extract keywords from job description using AI
        job_keywords = self._extract_job_keywords(job_description)
        if not job_keywords:
            # Fallback to simple extraction
            job_keywords = self._simple_keyword_extraction(job_description)

        # Extract keywords from resume
        resume_keywords = self._extract_resume_keywords(resume_data)

        # Find matches
        matching_keywords = set(job_keywords) & set(resume_keywords)
        missing_keywords = set(job_keywords) - set(resume_keywords)

        # Calculate score based on match percentage
        if job_keywords:
            match_ratio = len(matching_keywords) / len(job_keywords)
            points = int(30 * match_ratio)
        else:
            points = 30  # Full points if no keywords to match

        details.append(f"Job keywords found: {len(job_keywords)}")
        details.append(f"Matching keywords: {len(matching_keywords)}")

        if matching_keywords:
            top_matches = sorted(matching_keywords, key=len, reverse=True)[:5]
            details.append(f"Top matches: {', '.join(top_matches)}")

        if missing_keywords:
            missing_list = sorted(missing_keywords, key=len, reverse=True)[:5]
            details.append(f"Missing keywords: {', '.join(missing_list)}")
            suggestions.append(
                f"Add these keywords to skills or experience: {', '.join(missing_list)}"
            )

        return ATSCategoryScore(
            name="Keywords",
            points_earned=points,
            points_possible=30,
            details=details,
            suggestions=suggestions,
        )

    def _check_section_structure(self, resume_data: Dict[str, Any]) -> ATSCategoryScore:
        """
        Check if resume has standard ATS sections.

        Score: 20 points
        """
        points = 0
        details = []
        suggestions = []

        required_sections = {
            "experience": resume_data.get("experience"),
            "education": resume_data.get("education"),
            "skills": resume_data.get("skills"),
            "summary": resume_data.get("summary"),
        }

        for section_name, section_data in required_sections.items():
            if section_data:
                if section_name == "summary" and isinstance(section_data, str):
                    if section_data.strip():
                        points += 5
                        details.append(f"✓ {section_name.capitalize()} section present")
                elif isinstance(section_data, (list, dict)):
                    if section_data:
                        points += 5
                        details.append(f"✓ {section_name.capitalize()} section present")
            else:
                suggestions.append(f"Add {section_name.capitalize()} section")

        # Bonus points for ordering (Experience first is preferred)
        if required_sections.get("experience"):
            details.append("✓ Experience section present (ATS prefers first)")

        return ATSCategoryScore(
            name="Section Structure",
            points_earned=points,
            points_possible=20,
            details=details,
            suggestions=suggestions,
        )

    def _check_contact_info(self, resume_data: Dict[str, Any]) -> ATSCategoryScore:
        """
        Check contact information completeness.

        Score: 15 points
        """
        points = 0
        details = []
        suggestions = []

        contact = resume_data.get("contact", {})

        # Check required contact fields
        contact_fields = {
            "email": (contact.get("email"), 5, r"^[^@]+@[^@]+\.[^@]+$"),
            "phone": (contact.get("phone"), 5, r"\d"),
            "location": (contact.get("location"), 5, None),  # Just presence check
        }

        for field_name, (field_value, field_points, pattern) in contact_fields.items():
            if field_value:
                if pattern:
                    if re.search(pattern, field_value):
                        points += field_points
                        details.append(f"✓ {field_name.capitalize()} present and valid")
                    else:
                        details.append(f"⚠ {field_name.capitalize()} present but may be invalid")
                        suggestions.append(f"Fix {field_name} format")
                else:
                    points += field_points
                    details.append(f"✓ {field_name.capitalize()} present")
            else:
                suggestions.append(f"Add {field_name.capitalize()}")

        # Bonus: Check for LinkedIn/GitHub
        if contact.get("linkedin") or contact.get("github"):
            details.append("✓ Professional links (LinkedIn/GitHub) present")

        return ATSCategoryScore(
            name="Contact Info",
            points_earned=points,
            points_possible=15,
            details=details,
            suggestions=suggestions,
        )

    def _check_readability(self, resume_data: Dict[str, Any]) -> ATSCategoryScore:
        """
        Check resume readability and clarity.

        Score: 15 points
        """
        points = 15
        details = []
        suggestions = []

        all_text = self._get_all_text(resume_data)

        # Check for action verbs in experience bullets
        action_verbs = [
            "developed",
            "implemented",
            "built",
            "created",
            "designed",
            "managed",
            "led",
            "increased",
            "decreased",
            "improved",
            "achieved",
        ]
        action_verb_count = sum(1 for verb in action_verbs if verb in all_text.lower())

        if action_verb_count >= 3:
            details.append(f"✓ Uses action verbs ({action_verb_count} found)")
        else:
            points -= 5
            suggestions.append("Use more action verbs (e.g., developed, implemented)")

        # Check for quantifiable achievements
        has_numbers = bool(re.search(r"\d+%|\$\d+|\d+\s*(users|customers|projects)", all_text))
        if has_numbers:
            details.append("✓ Includes quantifiable achievements")
        else:
            points -= 3
            suggestions.append("Add quantifiable metrics (e.g., 'increased by 30%')")

        # Check for acronyms (should be minimal or defined)
        # This is a simple heuristic
        acronym_pattern = r"\b[A-Z]{2,4}\b"
        acronyms = re.findall(acronym_pattern, all_text)
        if len(acronyms) < 10:
            details.append(f"✓ Minimal acronyms ({len(acronyms)} found)")
        else:
            points -= 2
            details.append(f"⚠ Many acronyms detected ({len(acronyms)} found)")
            suggestions.append("Define acronyms or use full terms")

        # Check bullet point consistency
        experience = resume_data.get("experience", [])
        has_bullets = any(job.get("bullets") for job in experience)
        if has_bullets:
            details.append("✓ Uses bullet points for experience")
        else:
            points -= 5
            suggestions.append("Use bullet points for better readability")

        return ATSCategoryScore(
            name="Readability",
            points_earned=max(0, points),
            points_possible=15,
            details=details,
            suggestions=suggestions,
        )

    def _get_all_text(self, resume_data: Dict[str, Any]) -> str:
        """Extract all text from resume data."""
        text_parts = []

        def extract_value(value):
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    extract_value(item)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_value(v)

        extract_value(resume_data)
        return " ".join(text_parts).lower()

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """
        Extract keywords from job description using AI or fallback methods.

        Args:
            job_description: Job description text

        Returns:
            List of keyword strings
        """
        # Use AI if available
        if self.ai_available:
            prompt = f"""Extract the key technical skills, technologies, tools, and qualifications from this job posting.

**Job Description:**
{job_description}

**Instructions:**
- Extract ONLY specific technical skills, technologies, programming languages, frameworks, and tools
- Include soft skills if they are explicitly required (e.g., "communication", "leadership")
- Use lowercase for all keywords
- Prioritize the most important/mentioned items
- Return at most 20 keywords
- Return ONLY a JSON array of strings, nothing else

Example output:
["python", "machine learning", "aws", "kubernetes", "communication", "team leadership"]

Please extract the keywords:"""

            try:
                if self.provider == "anthropic":
                    response = self._call_anthropic(prompt)
                else:
                    response = self._call_openai(prompt)

                # Parse JSON from response
                json_match = re.search(r"\[.*\]", response, re.DOTALL)
                if json_match:
                    keywords = json.loads(json_match.group(0))
                    if isinstance(keywords, list):
                        return [str(k).lower().strip() for k in keywords if k][:20]

            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] AI keyword extraction failed: {str(e)}")

        # Fallback to simple keyword extraction
        return self._simple_keyword_extraction(job_description)

    def _extract_resume_keywords(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from resume data.

        Args:
            resume_data: Resume data dictionary

        Returns:
            List of keyword strings
        """
        keywords = []

        # Extract from skills
        skills = resume_data.get("skills", {})
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    if isinstance(skill, str):
                        keywords.append(skill.lower())
                    elif isinstance(skill, dict):
                        keywords.append(skill.get("name", "").lower())

        # Extract from experience bullets
        experience = resume_data.get("experience", [])
        for job in experience:
            for bullet in job.get("bullets", []):
                if isinstance(bullet, dict):
                    text = bullet.get("text", "").lower()
                    # Extract common tech terms from text
                    # This is a simple heuristic - AI could do better
                    keywords.extend(re.findall(r"\b[a-z]+(?:\s+[a-z]+)?\b", text))

        # Extract from summary
        summary = resume_data.get("summary", "")
        if summary:
            keywords.extend(re.findall(r"\b[a-z]{2,}\b", summary.lower()))

        return list(set(k.strip() for k in keywords if len(k) > 2))

    def _simple_keyword_extraction(self, job_description: str) -> List[str]:
        """
        Simple fallback keyword extraction without AI.

        Args:
            job_description: Job description text

        Returns:
            List of keyword strings
        """
        # Common tech keywords to look for
        common_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "node.js",
            "django",
            "flask",
            "fastapi",
            "kubernetes",
            "docker",
            "aws",
            "gcp",
            "azure",
            "sql",
            "mongodb",
            "postgresql",
            "redis",
            "ci/cd",
            "devops",
            "machine learning",
            "ai",
            "llm",
            "pytorch",
            "tensorflow",
            "react native",
            "graphql",
            "rest api",
            "microservices",
            "java",
            "go",
            "rust",
            "c++",
            "c#",
            ".net",
            "spring",
            "hibernate",
            "agile",
            "scrum",
            "kanban",
            "leadership",
            "communication",
            "teamwork",
        ]

        jd_lower = job_description.lower()
        found = [kw for kw in common_keywords if kw in jd_lower]

        return found

    def _generate_summary(
        self, categories: Dict[str, ATSCategoryScore], total_score: int, total_possible: int
    ) -> Tuple[str, List[str]]:
        """
        Generate summary and recommendations.

        Args:
            categories: Category scores
            total_score: Total score
            total_possible: Total possible score

        Returns:
            Tuple of (summary, recommendations)
        """
        percentage = (total_score / total_possible * 100) if total_possible else 0

        # Generate summary based on score
        if percentage >= 85:
            summary = "Excellent! Your resume is highly ATS-optimized."
        elif percentage >= 70:
            summary = "Good! Your resume is ATS-friendly with room for improvement."
        elif percentage >= 50:
            summary = "Fair. Some optimizations needed for better ATS compatibility."
        else:
            summary = "Poor. Your resume needs significant ATS optimization."

        # Collect all suggestions
        all_suggestions = []
        for cat in categories.values():
            all_suggestions.extend(cat.suggestions)

        # Prioritize suggestions (unique items)
        priority_suggestions = list(dict.fromkeys(all_suggestions))[:5]

        return summary, priority_suggestions

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        if not self.client:
            raise ValueError("AI client not available")

        model = self.config.ai_model

        message = self.client.messages.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 2000),
            temperature=self.config.get("ai.temperature", 0.3),
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        if not self.client:
            raise ValueError("AI client not available")

        model = self.config.ai_model

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 2000),
            temperature=self.config.get("ai.temperature", 0.3),
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    def print_report(self, report: ATSReport) -> None:
        """
        Print formatted ATS report to console.

        Args:
            report: ATSReport object to print
        """
        # Overall score
        score_color = (
            "green"
            if report.overall_percentage >= 70
            else "yellow" if report.overall_percentage >= 50 else "red"
        )
        score_text = Text(
            f"ATS Score: {report.total_score}/{report.total_possible} ({report.overall_percentage:.0f}%)"
        )
        score_text.stylize(f"bold {score_color}")

        console.print(Panel(score_text, title="ATS Compatibility Report", padding=1))

        # Summary
        console.print(f"\n[bold]{report.summary}[/bold]")

        # Category breakdown
        console.print("\n[bold]Category Breakdown:[/bold]")
        for cat_name, category in report.categories.items():
            # Determine checkmark or cross
            status = "✓" if category.points_earned == category.points_possible else "✗"

            # Color based on score
            if category.percentage >= 80:
                color = "green"
            elif category.percentage >= 50:
                color = "yellow"
            else:
                color = "red"

            # Print category header
            console.print(
                f"\n{status} [bold]{category.name}:[/bold] "
                f"{category.points_earned}/{category.points_possible} ({category.percentage:.0f}%)",
                style=color,
            )

            # Print details
            for detail in category.details:
                console.print(f"  {detail}")

            # Print suggestions
            if category.suggestions:
                console.print("  [yellow]Suggestions:[/yellow]")
                for suggestion in category.suggestions:
                    console.print(f"    • {suggestion}")

        # Top recommendations
        if report.recommendations:
            console.print("\n[bold]Top Recommendations:[/bold]")
            for i, rec in enumerate(report.recommendations, 1):
                console.print(f"  {i}. {rec}")

    def export_json(self, report: ATSReport, output_path: Path) -> None:
        """
        Export ATS report as JSON.

        Args:
            report: ATSReport object to export
            output_path: Path to save JSON file
        """
        # Convert to dict
        report_dict = {
            "total_score": report.total_score,
            "total_possible": report.total_possible,
            "overall_percentage": report.overall_percentage,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "categories": {name: asdict(cat) for name, cat in report.categories.items()},
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
