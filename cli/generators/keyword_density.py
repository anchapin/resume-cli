"""Keyword density analysis for resumes."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
class KeywordInfo:
    """Information about a single keyword."""

    keyword: str
    importance: str  # "high", "medium", "low"
    count: int
    is_present: bool
    suggested_sections: List[str]


@dataclass
class KeywordDensityReport:
    """Complete keyword density analysis report."""

    job_title: str
    company: str
    top_keywords: List[KeywordInfo]
    density_score: int  # 0-100
    present_count: int
    missing_count: int
    suggestions: List[str]


class KeywordDensityGenerator:
    """Generate keyword density analysis for resumes."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize keyword density generator.

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

    def generate_report(
        self, job_description: str, variant: Optional[str] = None
    ) -> KeywordDensityReport:
        """
        Generate keyword density analysis report.

        Args:
            job_description: Job description text
            variant: Resume variant to analyze (optional)

        Returns:
            KeywordDensityReport object with analysis
        """
        # Extract job details
        job_title, company = self._extract_job_details(job_description)

        # Extract keywords from job description using AI
        job_keywords_with_importance = self._extract_job_keywords(job_description)

        # Get resume data
        resume_data = self._get_resume_data(variant)

        # Count keyword occurrences in resume
        keyword_counts = self._count_keywords_in_resume(job_keywords_with_importance, resume_data)

        # Build keyword info list
        top_keywords = []
        present_count = 0
        missing_count = 0

        for keyword, importance in job_keywords_with_importance:
            count = keyword_counts.get(keyword, 0)
            is_present = count > 0

            if is_present:
                present_count += 1
            else:
                missing_count += 1

            # Suggest sections for missing keywords
            suggested_sections = self._suggest_sections_for_keyword(
                keyword, resume_data, is_present
            )

            top_keywords.append(
                KeywordInfo(
                    keyword=keyword,
                    importance=importance,
                    count=count,
                    is_present=is_present,
                    suggested_sections=suggested_sections,
                )
            )

        # Calculate density score
        total_keywords = len(job_keywords_with_importance)
        if total_keywords > 0:
            density_score = int((present_count / total_keywords) * 100)
        else:
            density_score = 0

        # Generate suggestions for missing keywords
        suggestions = self._generate_suggestions([kw for kw in top_keywords if not kw.is_present])

        return KeywordDensityReport(
            job_title=job_title or "Unknown Position",
            company=company or "Unknown Company",
            top_keywords=top_keywords,
            density_score=density_score,
            present_count=present_count,
            missing_count=missing_count,
            suggestions=suggestions,
        )

    def _extract_job_details(self, job_description: str) -> Tuple[str, str]:
        """Extract job title and company from job description."""
        job_title = ""
        company = ""

        # Try to extract job title (common patterns)
        title_patterns = [
            r"(?:job title|position|title):\s*([^\n]+)",
            r"^([^\n]+)\s*[-|]\s*[^|]+$",
            r"#\s*([^\n]+)",  # Markdown headers often have job title
        ]

        for pattern in title_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE | re.MULTILINE)
            if match:
                job_title = match.group(1).strip()
                break

        # Try to extract company name
        company_patterns = [
            r"(?:company|organization):\s*([^\n]+)",
            r"(?:at|from)\s+([A-Z][^\n]+?)(?:\s+[-\u2014]|\s+$)",
        ]

        for pattern in company_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                break

        return job_title, company

    def _extract_job_keywords(self, job_description: str) -> List[Tuple[str, str]]:
        """
        Extract keywords from job description with importance levels.

        Returns:
            List of tuples (keyword, importance)
        """
        # Use AI if available
        if self.ai_available:
            prompt = f"""Extract the key technical skills, technologies, tools, and qualifications from this job posting.

**Job Description:**
{job_description}

**Instructions:**
- Extract ONLY specific technical skills, technologies, programming languages, frameworks, and tools
- Include soft skills if they are explicitly required (e.g., "communication", "leadership")
- Assign importance level: "high" for explicitly mentioned/required, "medium" for preferred/nice-to-have
- Use lowercase for all keywords
- Return at most 20 keywords
- Return ONLY a JSON array of objects with "keyword" and "importance" fields, nothing else

Example output:
[{{"keyword": "python", "importance": "high"}}, {{"keyword": "machine learning", "importance": "high"}}, {{"keyword": "aws", "importance": "medium"}}]

Please extract the keywords:"""

            try:
                if self.provider == "anthropic":
                    response = self._call_anthropic(prompt)
                else:
                    response = self._call_openai(prompt)

                # Parse JSON from response
                json_match = re.search(r"\[.*\]", response, re.DOTALL)
                if json_match:
                    keywords_data = json.loads(json_match.group(0))
                    if isinstance(keywords_data, list):
                        return [
                            (
                                str(kw.get("keyword", "")).lower().strip(),
                                kw.get("importance", "medium"),
                            )
                            for kw in keywords_data
                            if kw.get("keyword")
                        ][:20]

            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] AI keyword extraction failed: {str(e)}")

        # Fallback to simple extraction
        return self._simple_keyword_extraction(job_description)

    def _simple_keyword_extraction(self, job_description: str) -> List[Tuple[str, str]]:
        """Simple fallback keyword extraction without AI."""
        common_keywords = [
            ("python", "high"),
            ("javascript", "high"),
            ("typescript", "high"),
            ("react", "high"),
            ("vue", "medium"),
            ("angular", "medium"),
            ("node.js", "high"),
            ("django", "medium"),
            ("flask", "medium"),
            ("fastapi", "medium"),
            ("kubernetes", "high"),
            ("docker", "high"),
            ("aws", "high"),
            ("gcp", "medium"),
            ("azure", "medium"),
            ("sql", "high"),
            ("mongodb", "medium"),
            ("postgresql", "medium"),
            ("redis", "medium"),
            ("ci/cd", "high"),
            ("devops", "high"),
            ("machine learning", "high"),
            ("ai", "high"),
            ("llm", "high"),
            ("pytorch", "medium"),
            ("tensorflow", "medium"),
            ("react native", "medium"),
            ("graphql", "medium"),
            ("rest api", "high"),
            ("microservices", "high"),
            ("java", "high"),
            ("go", "medium"),
            ("rust", "medium"),
            ("c++", "medium"),
            ("c#", "medium"),
            (".net", "medium"),
            ("spring", "medium"),
            ("hibernate", "medium"),
            ("agile", "high"),
            ("scrum", "medium"),
            ("kanban", "medium"),
            ("leadership", "high"),
            ("communication", "high"),
            ("teamwork", "medium"),
        ]

        jd_lower = job_description.lower()
        found = []

        for kw, importance in common_keywords:
            if kw in jd_lower:
                found.append((kw, importance))

        return found

    def _get_resume_data(self, variant: Optional[str]) -> Dict[str, Any]:
        """Get resume data for variant."""
        return {
            "summary": self.yaml_handler.get_summary(variant),
            "skills": self.yaml_handler.get_skills(variant),
            "experience": self.yaml_handler.get_experience(variant),
            "education": self.yaml_handler.get_education(variant),
            "projects": self.yaml_handler.get_projects(variant),
        }

    def _count_keywords_in_resume(
        self, keywords: List[Tuple[str, str]], resume_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Count occurrences of keywords in resume."""
        counts = {}

        # Get all resume text
        all_text = self._get_all_text(resume_data)

        for keyword, _ in keywords:
            # Count occurrences (case-insensitive)
            count = len(re.findall(rf"\b{re.escape(keyword)}\b", all_text, re.IGNORECASE))
            counts[keyword] = count

        return counts

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
        return " ".join(text_parts)

    def _suggest_sections_for_keyword(
        self, keyword: str, resume_data: Dict[str, Any], is_present: bool
    ) -> List[str]:
        """Suggest sections where a keyword could be added."""
        if is_present:
            return []

        suggestions = []

        # Check if keyword is tech-related
        tech_keywords = [
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
        ]

        if keyword.lower() in tech_keywords:
            suggestions.append("Skills section")

        # Check experience bullets
        experience = resume_data.get("experience", [])
        if experience:
            suggestions.append("Work experience bullets")

        # Check projects
        projects = resume_data.get("projects", {})
        if projects:
            suggestions.append("Projects section")

        return suggestions if suggestions else ["Skills or experience section"]

    def _generate_suggestions(self, missing_keywords: List[KeywordInfo]) -> List[str]:
        """Generate actionable suggestions for missing keywords."""
        suggestions = []

        # Group by importance
        high_importance = [kw for kw in missing_keywords if kw.importance == "high"]
        medium_importance = [kw for kw in missing_keywords if kw.importance == "medium"]

        if high_importance:
            high_names = ", ".join(kw.keyword for kw in high_importance[:3])
            suggestions.append(
                f"Add these high-priority keywords to skills or experience: {high_names}"
            )

        if medium_importance:
            medium_names = ", ".join(kw.keyword for kw in medium_importance[:3])
            suggestions.append(f"Consider adding these keywords: {medium_names}")

        return suggestions

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

    def print_report(self, report: KeywordDensityReport) -> None:
        """Print formatted keyword density report to console."""
        # Header
        title = f"Keyword Analysis for: {report.job_title} at {report.company}"
        score_color = (
            "green"
            if report.density_score >= 70
            else "yellow" if report.density_score >= 50 else "red"
        )
        score_text = f"Overall Density Score: {report.density_score}/100"
        score_panel = Panel(
            score_text,
            title="Keyword Density Analysis",
            border_style=score_color,
            padding=1,
        )
        console.print(score_panel)
        console.print()

        # Summary stats
        console.print(f"[bold]Job:[/bold] {report.job_title} at {report.company}")
        console.print(f"[bold]Present:[/bold] {report.present_count} keywords")
        console.print(f"[bold]Missing:[/bold] {report.missing_count} keywords")
        console.print()

        # Keyword table
        table = Table(title="Top Keywords from Job Description")
        table.add_column("#", style="dim", width=3)
        table.add_column("Keyword", style="cyan")
        table.add_column("Importance", style="yellow")
        table.add_column("Count", style="green")
        table.add_column("Status", style="white")

        for i, kw in enumerate(report.top_keywords, 1):
            status = (
                f"[green]✓ Present ({kw.count}x)[/green]"
                if kw.is_present
                else "[red]✗ Missing[/red]"
            )
            table.add_row(
                str(i),
                kw.keyword,
                kw.importance,
                str(kw.count) if kw.is_present else "0",
                status,
            )

        console.print(table)

        # Suggestions
        if report.suggestions:
            console.print("\n[bold]Suggestions:[/bold]")
            for suggestion in report.suggestions:
                console.print(f"  • {suggestion}")

        # Missing keywords details
        missing = [kw for kw in report.top_keywords if not kw.is_present]
        if missing:
            console.print("\n[bold red]Missing Keywords - Where to Add:[/bold red]")
            for kw in missing[:5]:
                sections = ", ".join(kw.suggested_sections)
                console.print(f"  • {kw.keyword} ({kw.importance}): Add to {sections}")

    def export_json(self, report: KeywordDensityReport, output_path: Path) -> None:
        """Export keyword density report as JSON."""
        report_dict = {
            "job_title": report.job_title,
            "company": report.company,
            "density_score": report.density_score,
            "present_count": report.present_count,
            "missing_count": report.missing_count,
            "suggestions": report.suggestions,
            "keywords": [
                {
                    "keyword": kw.keyword,
                    "importance": kw.importance,
                    "count": kw.count,
                    "is_present": kw.is_present,
                    "suggested_sections": kw.suggested_sections,
                }
                for kw in report.top_keywords
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
