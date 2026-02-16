#!/usr/bin/env python3
"""
Job Posting Parser
Parses job postings from LinkedIn, Indeed, and other sources to extract structured data.
"""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class JobDetails:
    """Structured job posting data."""

    company: str
    position: str
    requirements: List[str]
    responsibilities: List[str]
    salary: Optional[str] = None
    remote: Optional[bool] = None
    location: Optional[str] = None
    url: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class JobParser:
    """Parse job postings from various sources."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize job parser with optional cache directory."""
        self.cache_dir = cache_dir or Path.home() / ".resume-cli" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def parse_from_file(self, file_path: Path) -> JobDetails:
        """Parse job posting from HTML file."""
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return self._parse_html(content)

    def parse_from_url(self, url: str) -> JobDetails:
        """Parse job posting from URL.

        Note: For actual URL fetching, you'd need to implement HTTP requests.
        This is a simplified version that returns mock data for demonstration.
        """
        # Check cache first
        cache_key = self._get_cache_key(url)
        cached = self._get_from_cache(cache_key)
        if cached:
            console.print(f"[dim]Using cached data for {url}[/dim]")
            return cached

        # For now, raise an error - actual implementation would fetch the URL
        raise NotImplementedError(
            "URL fetching requires implementing HTTP client. "
            "For now, use --file to parse local HTML files."
        )

    def _parse_html(self, html: str) -> JobDetails:
        """Parse HTML content to extract job details."""
        # Try to detect the source (LinkedIn, Indeed, etc.)
        if "linkedin.com" in html.lower() or self._has_linkedin_structure(html):
            return self._parse_linkedin(html)
        elif "indeed.com" in html.lower() or self._has_indeed_structure(html):
            return self._parse_indeed(html)
        else:
            return self._parse_generic(html)

    def _has_linkedin_structure(self, html: str) -> bool:
        """Check if HTML has LinkedIn structure."""
        return "linkedin" in html.lower() or "job-details" in html.lower()

    def _has_indeed_structure(self, html: str) -> bool:
        """Check if HTML has Indeed structure."""
        return "indeed" in html.lower() or "jobsearch" in html.lower()

    def _parse_linkedin(self, html: str) -> JobDetails:
        """Parse LinkedIn job posting."""
        # Extract company
        company = self._extract_pattern(
            html, r'(?:company|employer)["\s:]+([^"<>\n]+)', default="Unknown Company"
        )

        # Extract position
        position = self._extract_pattern(html, r"<h1[^>]*>([^<]+)</h1>", default="Unknown Position")

        # Extract requirements (skills, qualifications)
        requirements = self._extract_list(
            html,
            r"(?:requirements?|qualifications?|skills?)[^.]*?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
            max_items=10,
        )

        # Extract responsibilities
        responsibilities = self._extract_list(
            html, r"(?:responsibilities?|duties?|what you\'ll do)[^.]*?([A-Z][^.<>]+)", max_items=10
        )

        # Extract salary
        salary = self._extract_pattern(
            html,
            r"\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:hour|year|month|annum))?",
        )

        # Extract location
        location = self._extract_pattern(
            html,
            r"(?:location|remote|hybrid)[^,<>\n]*([^,<>\n]+)",
        )

        # Detect remote
        remote = bool(re.search(r"\bremote\b", html, re.IGNORECASE))

        return JobDetails(
            company=company.strip(),
            position=position.strip(),
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
            remote=remote,
            location=location.strip() if location else None,
        )

    def _parse_indeed(self, html: str) -> JobDetails:
        """Parse Indeed job posting."""
        # Extract company
        company = self._extract_pattern(
            html, r'company["\s:]+([^"<>\n]+)', default="Unknown Company"
        )

        # Extract position
        position = self._extract_pattern(html, r"<h1[^>]*>([^<]+)</h1>", default="Unknown Position")

        # Extract requirements
        requirements = self._extract_list(
            html,
            r"(?:requirements?|qualifications?)[^.]*?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
            max_items=10,
        )

        # Extract responsibilities
        responsibilities = self._extract_list(
            html, r"(?:responsibilities?|duties?)[^.]*?([A-Z][^.<>]+)", max_items=10
        )

        # Extract salary
        salary = self._extract_pattern(
            html,
            r"\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:hour|year|month|annum))?",
        )

        # Extract location
        location = self._extract_pattern(
            html,
            r'location["\s:]+([^"<>\n]+)',
        )

        # Detect remote
        remote = bool(re.search(r"\bremote\b", html, re.IGNORECASE))

        return JobDetails(
            company=company.strip(),
            position=position.strip(),
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
            remote=remote,
            location=location.strip() if location else None,
        )

    def _parse_generic(self, html: str) -> JobDetails:
        """Parse generic job posting (fallback)."""
        # Try to extract common patterns
        company = self._extract_pattern(
            html, r'(?:company|employer|organization)["\s:]+([^"<>\n]+)', default="Unknown Company"
        )

        position = self._extract_pattern(
            html, r"<h[1-3][^>]*>([^<]+)</h[1-3]>", default="Unknown Position"
        )

        # Look for sections
        requirements = []
        responsibilities = []

        # Try to find requirements section
        req_match = re.search(
            r"(?:requirements|qualifications|what we\'re looking for)[:\s]*(.+?)(?=<h|$)",
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if req_match:
            requirements = self._extract_items_from_text(req_match.group(1))

        # Try to find responsibilities section
        resp_match = re.search(
            r"(?:responsibilities|duties|what you\'ll do)[:\s]*(.+?)(?=<h|$)",
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if resp_match:
            responsibilities = self._extract_items_from_text(resp_match.group(1))

        # Extract salary if present
        salary = self._extract_pattern(
            html,
            r"(\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:hour|year|month|annum))?)",
        )

        return JobDetails(
            company=company.strip(),
            position=position.strip(),
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
        )

    def _extract_pattern(self, text: str, pattern: str, default: str = "") -> str:
        """Extract text using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default

    def _extract_list(self, text: str, pattern: str, max_items: int = 10) -> List[str]:
        """Extract list of items using regex pattern."""
        matches = re.findall(pattern, text, re.IGNORECASE)
        # Deduplicate and limit
        seen = set()
        items = []
        for match in matches:
            item = match.strip()
            if item and item.lower() not in seen and len(item) > 2:
                seen.add(item.lower())
                items.append(item)
                if len(items) >= max_items:
                    break
        return items

    def _extract_items_from_text(self, text: str) -> List[str]:
        """Extract list items from text (bullets, numbered lists, etc.)."""
        items = []
        # Match bullet points, numbered lists, or comma-separated items
        patterns = [
            r"[•\-\*]\s*([^\n]+)",  # Bullet points
            r"\d+\.\s*([^\n]+)",  # Numbered lists
            r",\s*(?=[A-Z])",  # Comma-separated (capitalized)
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                items = [m.strip() for m in matches if m.strip()]
                break

        return items[:10]  # Limit to 10 items

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        import hashlib

        return hashlib.sha256(url.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[JobDetails]:
        """Get cached job details."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                return JobDetails(**data)
            except Exception:
                return None
        return None

    def _save_to_cache(self, cache_key: str, job_details: JobDetails):
        """Save job details to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(job_details.to_json())


def parse_job_posting(
    file_path: Optional[Path] = None,
    url: Optional[str] = None,
    output: Optional[Path] = None,
    use_cache: bool = True,
) -> JobDetails:
    """Parse job posting from file or URL."""
    parser = JobParser() if use_cache else JobParser(cache_dir=Path("/dev/null"))

    if file_path:
        job_details = parser.parse_from_file(Path(file_path))
    elif url:
        job_details = parser.parse_from_url(url)
    else:
        raise ValueError("Either --file or --url must be provided")

    # Save to cache if enabled
    if use_cache and url:
        cache_key = parser._get_cache_key(url)
        parser._save_to_cache(cache_key, job_details)

    return job_details
