#!/usr/bin/env python3
"""
Job Posting Parser for LinkedIn, Indeed, and other sources.

Parses job postings from HTML files or URLs and extracts structured data:
- Company name
- Position title
- Requirements/qualifications
- Responsibilities
- Salary information
- Remote status
- Location

Outputs structured JSON for use with AI resume tailoring.
"""

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag


@dataclass
class JobDetails:
    """Structured job posting data."""

    company: str = ""
    position: str = ""
    requirements: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    salary: Optional[str] = None
    remote: Optional[bool] = None
    location: Optional[str] = None
    url: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    description: Optional[str] = None
    benefits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobDetails":
        """Create JobDetails from dictionary."""
        return cls(
            company=data.get("company", ""),
            position=data.get("position", ""),
            requirements=data.get("requirements", []),
            responsibilities=data.get("responsibilities", []),
            salary=data.get("salary"),
            remote=data.get("remote"),
            location=data.get("location"),
            url=data.get("url"),
            job_type=data.get("job_type"),
            experience_level=data.get("experience_level"),
            description=data.get("description"),
            benefits=data.get("benefits", []),
        )


class JobParser:
    """Parse job postings from LinkedIn, Indeed, and other sources."""

    # LinkedIn-specific selectors and patterns
    LINKEDIN_SELECTORS = {
        "company": [
            "[data-test-company-name]",
            ".company-name",
            "[data-organization-name]",
            ".job-details-job-university-recruiter__company-name",
            "h4.job-details-job-university-recruiter__company-name",
        ],
        "position": [
            "h1.topcard-layout__title",
            "h1.job-details-jobs-unified-top-card__job-title",
            "[data-test-job-title]",
            ".topcard__title",
            "h1[data-organization-job-title]",
        ],
        "location": [
            "[data-test-company-location]",
            ".job-details-jobs-unified-top-card__location",
            ".topcard__flavor--bullet",
            "[data-job-location]",
        ],
        "description": [
            "[data-test-job-description]",
            ".job-details__main-content",
            "#job-details",
            ".show-more-less-html__markup",
        ],
        "salary": [
            "[data-test-salary]",
            ".salary",
            ".job-details-jobs-unified-top-card__salary",
            "[data-job-salary]",
        ],
    }

    # Indeed-specific selectors and patterns
    INDEED_SELECTORS = {
        "company": [
            "[data-company-name]",
            ".company-name",
            "[data-tn-company-name]",
            "span[data-tn-element='companyName']",
            ".jobsearch-InlineCompanyRating",
        ],
        "position": [
            "h1.jobsearch-JobInfoHeader-title",
            "[data-job-title]",
            ".jobsearch-JobInfoHeader-title-container",
            "h1[data-tn-element='jobTitle']",
        ],
        "location": [
            "[data-tn-element='location']",
            ".jobsearch-JobInfoHeader-subtitle",
            ".jobsearch-CompanyReviewWithInlineLocation",
        ],
        "description": [
            "#jobDescriptionText",
            "[data-tn-element='jobDescription']",
            ".jobsearch-jobDescriptionText",
            "#jobDescriptionContainer",
        ],
        "salary": [
            "[data-tn-element='salaryInfo']",
            ".jobsearch-SalaryMessage",
            ".salary-text",
            "[data-job-salary]",
        ],
    }

    # Remote detection keywords
    REMOTE_KEYWORDS = [
        "remote",
        "work from home",
        "wfh",
        "distributed team",
        "virtual",
        "telecommute",
        "telecommuting",
        "100% remote",
        "fully remote",
        "remote-first",
        "remote friendly",
        "work remotely",
    ]

    # Hybrid detection keywords
    HYBRID_KEYWORDS = [
        "hybrid",
        "flexible location",
        "partially remote",
        "remote optional",
        "remote available",
    ]

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize job parser.

        Args:
            cache_dir: Directory for caching parsed job postings.
                      Defaults to ~/.resume-cli/cache/jobs
        """
        self.cache_dir = cache_dir or Path.home() / ".resume-cli" / "cache" / "jobs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def parse_from_file(self, file_path: Path, url: Optional[str] = None) -> JobDetails:
        """
        Parse job posting from HTML file.

        Args:
            file_path: Path to HTML file
            url: Optional URL to associate with the parsed data

        Returns:
            JobDetails with extracted information
        """
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        job_details = self._parse_html(content)
        if url:
            job_details.url = url
        return job_details

    def parse_from_url(self, url: str) -> JobDetails:
        """
        Parse job posting from URL.

        First checks cache for previously parsed data.
        If not cached, fetches the URL and parses the HTML.

        Args:
            url: URL to job posting

        Returns:
            JobDetails with extracted information
        """
        # Check cache first
        cache_key = self._get_cache_key(url)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        # Fetch and parse
        try:
            import requests

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            job_details = self._parse_html(response.text)
            job_details.url = url

            # Save to cache
            self._save_to_cache(cache_key, job_details)

            return job_details

        except ImportError:
            raise NotImplementedError(
                "URL fetching requires 'requests' library. Install with: pip install requests"
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")

    def _parse_html(self, html: str) -> JobDetails:
        """
        Parse HTML content and detect source automatically.

        Args:
            html: Raw HTML content

        Returns:
            JobDetails with extracted information
        """
        # Detect source
        if self._is_linkedin(html):
            return self._parse_linkedin(html)
        elif self._is_indeed(html):
            return self._parse_indeed(html)
        else:
            return self._parse_generic(html)

    def _is_linkedin(self, html: str) -> bool:
        """Check if HTML is from LinkedIn."""
        html_lower = html.lower()
        return (
            "linkedin.com" in html_lower
            or "linkedin" in html_lower
            or "topcard" in html_lower
            or "job-details-jobs-unified" in html_lower
            or 'data-test-company-name="' in html_lower
        )

    def _is_indeed(self, html: str) -> bool:
        """Check if HTML is from Indeed."""
        html_lower = html.lower()
        return (
            "indeed.com" in html_lower
            or "indeed" in html_lower
            or "jobsearch" in html_lower
            or "data-tn-element" in html_lower
            or "jobsearch-jobDescriptionText" in html_lower
        )

    def _parse_linkedin(self, html: str) -> JobDetails:
        """
        Parse LinkedIn job posting.

        Args:
            html: LinkedIn job posting HTML

        Returns:
            JobDetails with extracted information
        """
        soup = BeautifulSoup(html, "lxml")

        # Extract company
        company = self._extract_by_selectors(soup, self.LINKEDIN_SELECTORS["company"])
        if not company:
            # Fallback: look for common patterns
            company = self._extract_text_by_pattern(
                html, r'(?:company|employer|organization)["\s:]+([^"<>\n]+)'
            )

        # Extract position
        position = self._extract_by_selectors(soup, self.LINKEDIN_SELECTORS["position"])
        if not position:
            # Fallback to h1 tags
            h1 = soup.find("h1")
            position = h1.get_text(strip=True) if h1 else ""

        # Extract location
        location = self._extract_by_selectors(soup, self.LINKEDIN_SELECTORS["location"])

        # Extract description
        description_elem = self._find_by_selectors(soup, self.LINKEDIN_SELECTORS["description"])
        description = (
            description_elem.get_text(separator="\n", strip=True) if description_elem else ""
        )

        # Extract salary
        salary = self._extract_by_selectors(soup, self.LINKEDIN_SELECTORS["salary"])
        if not salary:
            salary = self._extract_salary_from_text(html)

        # Extract requirements and responsibilities from description
        requirements, responsibilities = self._extract_sections_from_description(description)

        # Detect remote status
        remote = self._detect_remote_status(html + " " + (description or ""))

        # Extract job type and experience level
        job_type = self._extract_job_type(html)
        experience_level = self._extract_experience_level(html)

        return JobDetails(
            company=company or "Unknown Company",
            position=position or "Unknown Position",
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
            remote=remote,
            location=location,
            description=description if description else None,
            job_type=job_type,
            experience_level=experience_level,
        )

    def _parse_indeed(self, html: str) -> JobDetails:
        """
        Parse Indeed job posting.

        Args:
            html: Indeed job posting HTML

        Returns:
            JobDetails with extracted information
        """
        soup = BeautifulSoup(html, "lxml")

        # Extract company
        company = self._extract_by_selectors(soup, self.INDEED_SELECTORS["company"])
        if not company:
            # Fallback patterns
            company = self._extract_text_by_pattern(html, r'company["\s:]+([^"<>\n]+)')

        # Extract position
        position = self._extract_by_selectors(soup, self.INDEED_SELECTORS["position"])
        if not position:
            h1 = soup.find("h1", class_=re.compile(r"jobsearch-JobInfoHeader"))
            position = h1.get_text(strip=True) if h1 else ""

        # Extract location
        location = self._extract_by_selectors(soup, self.INDEED_SELECTORS["location"])

        # Extract description
        description_elem = self._find_by_selectors(soup, self.INDEED_SELECTORS["description"])
        description = (
            description_elem.get_text(separator="\n", strip=True) if description_elem else ""
        )

        # Extract salary
        salary = self._extract_by_selectors(soup, self.INDEED_SELECTORS["salary"])
        if not salary:
            salary = self._extract_salary_from_text(html)

        # Extract requirements and responsibilities
        requirements, responsibilities = self._extract_sections_from_description(description)

        # Detect remote status
        remote = self._detect_remote_status(html + " " + (description or ""))

        # Extract job type and experience level
        job_type = self._extract_job_type(html)
        experience_level = self._extract_experience_level(html)

        return JobDetails(
            company=company or "Unknown Company",
            position=position or "Unknown Position",
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
            remote=remote,
            location=location,
            description=description if description else None,
            job_type=job_type,
            experience_level=experience_level,
        )

    def _parse_generic(self, html: str) -> JobDetails:
        """
        Parse generic job posting (fallback parser).

        Args:
            html: Generic job posting HTML

        Returns:
            JobDetails with extracted information
        """
        soup = BeautifulSoup(html, "lxml")

        # Try to extract company from various patterns
        company = self._extract_text_by_pattern(
            html, r'(?:company|employer|organization|hiring)[:\s]+([^"<>\n]+)'
        )
        if not company:
            # Look for company in meta tags
            meta_company = soup.find("meta", attrs={"name": "company"})
            if meta_company:
                company = meta_company.get("content", "")

        # Extract position from h1 or title
        position = ""
        h1 = soup.find("h1")
        if h1:
            position = h1.get_text(strip=True)
        if not position:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
                # Remove common suffixes
                position = re.sub(r"\s*[-|]\s*.*$", "", title)

        # Extract location
        location = self._extract_text_by_pattern(html, r"(?:location|based|office)[:\s]+([^<>\n]+)")

        # Extract salary
        salary = self._extract_salary_from_text(html)

        # Extract requirements section - look for heading tags first
        requirements = []
        req_heading = soup.find(
            ["h1", "h2", "h3", "h4", "h5", "h6"],
            string=re.compile(r"requirements|qualifications|skills", re.IGNORECASE),
        )
        if req_heading:
            # Get the next sibling element(s) containing the list
            next_elem = req_heading.find_next_sibling(["ul", "ol", "div", "p"])
            if next_elem:
                requirements = self._extract_list_items(next_elem)
        if not requirements:
            # Try to find by text pattern
            requirements = self._extract_list_by_keyword(html, "requirements")

        # Extract responsibilities section
        responsibilities = []
        resp_heading = soup.find(
            ["h1", "h2", "h3", "h4", "h5", "h6"],
            string=re.compile(r"responsibilities|duties|what you", re.IGNORECASE),
        )
        if resp_heading:
            next_elem = resp_heading.find_next_sibling(["ul", "ol", "div", "p"])
            if next_elem:
                responsibilities = self._extract_list_items(next_elem)
        if not responsibilities:
            responsibilities = self._extract_list_by_keyword(html, "responsibilities")

        # Detect remote status
        remote = self._detect_remote_status(html)

        # Extract job type and experience level
        job_type = self._extract_job_type(html)
        experience_level = self._extract_experience_level(html)

        return JobDetails(
            company=company or "Unknown Company",
            position=position or "Unknown Position",
            requirements=requirements,
            responsibilities=responsibilities,
            salary=salary,
            remote=remote,
            location=location,
            job_type=job_type,
            experience_level=experience_level,
        )

    def _extract_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """
        Extract text using multiple CSS selectors.

        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try

        Returns:
            Extracted text or None
        """
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text
        return None

    def _find_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[Tag]:
        """
        Find element using multiple CSS selectors.

        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try

        Returns:
            Found element or None
        """
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem
        return None

    def _extract_text_by_pattern(self, text: str, pattern: str) -> Optional[str]:
        """
        Extract text using regex pattern.

        Args:
            text: Text to search
            pattern: Regex pattern

        Returns:
            Extracted text or None
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_salary_from_text(self, text: str) -> Optional[str]:
        """
        Extract salary information from text.

        Args:
            text: Text to search

        Returns:
            Salary string or None
        """
        # Common salary patterns
        patterns = [
            r"\$[\d,]+(?:\s*[-–to]+\s*\$[\d,]+)?",  # $100k - $150k
            r"\$[\d,]+k(?:\s*[-–to]+\s*\$[\d,]+k)?",  # $100k - $150k
            r"[\d,]+k(?:\s*[-–to]+\s*[\d,]+k)",  # 100k - 150k
            r"(?:salary|pay|compensation)[:\s]*(\$[^<>\n]+)",  # Salary: $X
            r"(?:per|/)\s*(?:year|annum)[:\s]*(\$[^<>\n]+)",  # per year: $X
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(0) if match.lastindex is None else match.group(1)
                # Clean up the salary string
                salary = re.sub(r"\s+", " ", salary.strip())
                if "$" not in salary and re.search(r"\d+k", salary):
                    salary = "$" + salary
                return salary

        return None

    def _extract_sections_from_description(self, description: str) -> tuple[List[str], List[str]]:
        """
        Extract requirements and responsibilities from job description.

        Args:
            description: Job description text

        Returns:
            Tuple of (requirements, responsibilities)
        """
        requirements = []
        responsibilities = []

        if not description:
            return requirements, responsibilities

        # Find section boundaries using regex
        # Match section headers with optional colon, at start of line or after newline
        req_pattern = r"(?:^|\n)\s*(requirements?|qualifications?|what we(?:'re)? looking for|what you(?:'ll)? bring)\s*:?\s*\n"
        resp_pattern = r"(?:^|\n)\s*(responsibilities?|duties?|what you(?:'ll)? do|your impact|key responsibilities)\s*:?\s*\n"

        # Find positions of section headers
        req_match = re.search(req_pattern, description, re.IGNORECASE)
        resp_match = re.search(resp_pattern, description, re.IGNORECASE)

        req_start = req_match.start() if req_match else -1
        resp_start = resp_match.start() if resp_match else -1

        # Extract requirements section
        if req_start >= 0:
            # Find end of requirements section (start of responsibilities or end of text)
            if resp_start > req_start:
                req_section = description[req_start:resp_start]
            else:
                req_section = description[req_start:]

            # Extract list items from requirements section
            requirements = self._extract_items_from_text(req_section)

        # Extract responsibilities section
        if resp_start >= 0:
            # Find end of responsibilities section (look for next section or end)
            next_section_patterns = [
                r"(?:^|\n)\s*(benefits|compensation|perks|about|company|team)\s*:?\s*\n",
                r"(?:^|\n)\s*(requirements?|qualifications?)\s*:?\s*\n",
            ]
            resp_end = len(description)
            for pattern in next_section_patterns:
                next_match = re.search(pattern, description[resp_start:], re.IGNORECASE)
                if next_match:
                    resp_end = resp_start + next_match.start()
                    break

            resp_section = description[resp_start:resp_end]
            responsibilities = self._extract_items_from_text(resp_section)

        # Deduplicate
        requirements = list(dict.fromkeys(requirements))
        responsibilities = list(dict.fromkeys(responsibilities))

        return requirements[:15], responsibilities[:15]

    def _extract_items_from_text(self, text: str) -> List[str]:
        """
        Extract list items from text.

        Args:
            text: Text containing list items

        Returns:
            List of extracted items
        """
        items = []

        # Section header keywords to exclude - only match when line STARTS with these
        # (not when they appear in the middle of a sentence)
        section_header_starts = [
            "requirements",
            "qualifications",
            "responsibilities",
            "duties",
            "what you",
            "what we",
            "your impact",
            "key responsibilities",
            "benefits",
            "compensation",
            "perks",
            "about the",
            "about us",
            "company",
            "team",
            "our team",
            "the company",
        ]

        # Match bullet points
        bullet_patterns = [
            r"[•\-\*]\s*([^\n]+)",  # Standard bullets
            r"^\s*\d+[\.\)]\s*([^\n]+)",  # Numbered lists
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                items = [m.strip() for m in matches if m.strip() and len(m.strip()) > 5]
                break

        # If no bullets found, try extracting lines that look like list items
        if not items:
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # Skip empty lines and short lines
                if not line or len(line) < 5:
                    continue
                line_lower = line.lower()
                # Skip lines that start with section header keywords
                if any(
                    line_lower.startswith(header) or line_lower.startswith(header + ":")
                    for header in section_header_starts
                ):
                    continue
                # Skip lines that look like headers (all caps or very short)
                if line.isupper() and len(line) < 50:
                    continue
                items.append(line)

        # If still no items, try comma-separated
        if not items:
            parts = re.split(r",\s*(?=[A-Z])", text)
            items = [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]

        return items[:15]

    def _extract_list_items(self, element: Tag) -> List[str]:
        """
        Extract list items from a BeautifulSoup element.

        Args:
            element: BeautifulSoup element containing list

        Returns:
            List of item texts
        """
        items = []

        # Find all li elements
        li_elements = element.find_all("li")
        if li_elements:
            items = [li.get_text(strip=True) for li in li_elements if li.get_text(strip=True)]
        else:
            # Try to find bullet points in text
            text = element.get_text(separator="\n")
            items = self._extract_items_from_text(text)

        return [item for item in items if len(item) > 3][:15]

    def _extract_list_by_keyword(self, html: str, keyword: str) -> List[str]:
        """
        Extract list items near a keyword.

        Args:
            html: HTML content
            keyword: Keyword to search for

        Returns:
            List of extracted items
        """
        soup = BeautifulSoup(html, "lxml")

        # Find element containing the keyword
        for elem in soup.find_all(string=re.compile(keyword, re.IGNORECASE)):
            parent = elem.find_parent(["div", "section", "ul", "li"])
            if parent:
                # Look for list items in parent or siblings
                items = self._extract_list_items(parent)
                if items:
                    return items

                # Check next sibling
                next_sibling = parent.find_next_sibling(["ul", "div"])
                if next_sibling:
                    items = self._extract_list_items(next_sibling)
                    if items:
                        return items

        return []

    def _detect_remote_status(self, text: str) -> Optional[bool]:
        """
        Detect if position is remote.

        Args:
            text: Text to analyze

        Returns:
            True if remote, False if not remote, None if unclear
        """
        text_lower = text.lower()

        # Check for remote keywords
        for keyword in self.REMOTE_KEYWORDS:
            if keyword in text_lower:
                return True

        # Check for hybrid keywords
        for keyword in self.HYBRID_KEYWORDS:
            if keyword in text_lower:
                return True  # Consider hybrid as remote-friendly

        # Check for on-site only indicators
        onsite_keywords = ["on-site", "onsite", "in-office", "in person", "at our office"]
        for keyword in onsite_keywords:
            if keyword in text_lower and "remote" not in text_lower:
                return False

        return None

    def _extract_job_type(self, html: str) -> Optional[str]:
        """
        Extract job type (full-time, part-time, contract, etc.).

        Args:
            html: HTML content

        Returns:
            Job type string or None
        """
        patterns = [
            r"\b(full[- ]?time|part[- ]?time|contract|freelance|intern|temporary)\b",
            r"\b(permanent|fixed[- ]?term)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).lower().replace("-", "-")

        return None

    def _extract_experience_level(self, html: str) -> Optional[str]:
        """
        Extract experience level (entry, mid, senior, etc.).

        Args:
            html: HTML content

        Returns:
            Experience level string or None
        """
        patterns = [
            r"\b(entry[- ]?level|junior|mid[- ]?level|senior|staff|principal|lead)\b",
            r"\b(associate|vice[- ]?president|director|executive)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).lower().replace("-", "-")

        return None

    def _get_cache_key(self, url: str) -> str:
        """
        Generate cache key from URL.

        Args:
            url: Job posting URL

        Returns:
            Hash string for caching
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[JobDetails]:
        """
        Get cached job details.

        Args:
            cache_key: Cache key

        Returns:
            Cached JobDetails or None
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return JobDetails.from_dict(data)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _save_to_cache(self, cache_key: str, job_details: JobDetails) -> None:
        """
        Save job details to cache.

        Args:
            cache_key: Cache key
            job_details: JobDetails to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(job_details.to_json(), encoding="utf-8")

    def clear_cache(self) -> int:
        """
        Clear all cached job postings.

        Returns:
            Number of files cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count


def parse_job_posting(
    file_path: Optional[Path] = None,
    url: Optional[str] = None,
    output: Optional[Path] = None,
    use_cache: bool = True,
) -> JobDetails:
    """
    Parse job posting from file or URL.

    Convenience function for parsing job postings.

    Args:
        file_path: Path to HTML file
        url: URL to job posting
        output: Optional path to save JSON output
        use_cache: Whether to use caching

    Returns:
        JobDetails with extracted information

    Raises:
        ValueError: If neither file_path nor url is provided
    """
    cache_dir = None if not use_cache else None
    parser = JobParser(cache_dir=cache_dir)

    if file_path:
        job_details = parser.parse_from_file(Path(file_path))
    elif url:
        job_details = parser.parse_from_url(url)
    else:
        raise ValueError("Either file_path or url must be provided")

    # Save to output file if requested
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(job_details.to_json(), encoding="utf-8")

    return job_details
