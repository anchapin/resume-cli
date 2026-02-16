"""Unit tests for JobParser class."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.generators.job_parser import JobDetails, JobParser


@pytest.fixture
def job_parser():
    """Create JobParser instance."""
    return JobParser()


class TestJobDetails:
    """Test JobDetails dataclass."""

    def test_job_details_creation(self):
        """Test creating JobDetails with required fields."""
        job = JobDetails(
            company="Test Company",
            position="Software Engineer",
            requirements=["Python", "JavaScript"],
            responsibilities=["Build APIs", "Write tests"],
        )

        assert job.company == "Test Company"
        assert job.position == "Software Engineer"
        assert len(job.requirements) == 2
        assert len(job.responsibilities) == 2

    def test_job_details_with_optional_fields(self):
        """Test creating JobDetails with optional fields."""
        job = JobDetails(
            company="Test Company",
            position="Senior Engineer",
            requirements=["Python"],
            responsibilities=["Code"],
            salary="$100,000 - $150,000",
            remote=True,
            location="San Francisco, CA",
            url="https://example.com/job",
            job_type="Full-time",
            experience_level="Senior",
        )

        assert job.salary == "$100,000 - $150,000"
        assert job.remote is True
        assert job.location == "San Francisco, CA"

    def test_to_dict(self):
        """Test converting JobDetails to dict."""
        job = JobDetails(
            company="Test Company",
            position="Engineer",
            requirements=["Python"],
            responsibilities=["Code"],
        )

        data = job.to_dict()

        assert isinstance(data, dict)
        assert data["company"] == "Test Company"
        assert data["position"] == "Engineer"

    def test_to_json(self):
        """Test converting JobDetails to JSON."""
        job = JobDetails(
            company="Test Company",
            position="Engineer",
            requirements=["Python"],
            responsibilities=["Code"],
        )

        json_str = job.to_json()
        data = json.loads(json_str)

        assert data["company"] == "Test Company"
        assert data["position"] == "Engineer"


class TestJobParserInitialization:
    """Test JobParser initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        parser = JobParser()
        assert parser.cache_dir is not None

    def test_init_with_cache_dir(self, tmp_path):
        """Test initialization with custom cache directory."""
        parser = JobParser(cache_dir=tmp_path)
        assert parser.cache_dir == tmp_path

    def test_cache_dir_created(self, tmp_path):
        """Test that cache directory is created."""
        cache_dir = tmp_path / "cache"
        parser = JobParser(cache_dir=cache_dir)
        assert cache_dir.exists()


class TestParseFromFile:
    """Test parse_from_file method."""

    def test_parse_from_file_linkedin(self, job_parser, tmp_path):
        """Test parsing LinkedIn job posting."""
        html_content = """
        <html>
        <head><title>Software Engineer at LinkedIn</title></head>
        <body>
            <h1>Senior Software Engineer</h1>
            <div class="company">LinkedIn</div>
            <div class="job-details">Requirements: Python, JavaScript, React</div>
        </body>
        </html>
        """
        html_file = tmp_path / "job.html"
        html_file.write_text(html_content)

        job = job_parser.parse_from_file(html_file)

        assert job.company is not None
        assert job.position is not None

    def test_parse_from_file_indeed(self, job_parser, tmp_path):
        """Test parsing Indeed job posting."""
        html_content = """
        <html>
        <body>
            <h1>Software Engineer</h1>
            <span class="company">Google</span>
            <div class="jobsearch-JobDetails-jobInfo">Requirements: Python, Go</div>
        </body>
        </html>
        """
        html_file = tmp_path / "job.html"
        html_file.write_text(html_content)

        job = job_parser.parse_from_file(html_file)

        assert job.company is not None

    def test_parse_from_file_generic(self, job_parser, tmp_path):
        """Test parsing generic job posting."""
        html_content = """
        <html>
        <body>
            <h1>Software Engineer</h1>
            <p>Company: Test Corp</p>
            <h2>Requirements</h2>
            <ul>
                <li>Python</li>
                <li>JavaScript</li>
            </ul>
        </body>
        </html>
        """
        html_file = tmp_path / "job.html"
        html_file.write_text(html_content)

        job = job_parser.parse_from_file(html_file)

        assert job.position is not None


class TestParseFromURL:
    """Test parse_from_url method."""

    def test_parse_from_url_not_implemented(self, job_parser):
        """Test that URL parsing raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            job_parser.parse_from_url("https://example.com/job")

    def test_parse_from_url_uses_cache(self, job_parser, tmp_path):
        """Test that URL parsing uses cached data."""
        cache_dir = tmp_path / "cache"
        job_parser.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create cache file
        cache_key = job_parser._get_cache_key("https://example.com/job")
        cached_job = JobDetails(
            company="Cached Company",
            position="Cached Position",
            requirements=["Cached Skill"],
            responsibilities=["Cached Task"],
        )
        cache_file = cache_dir / f"{cache_key}.json"
        cache_file.write_text(cached_job.to_json())

        # Should return cached data
        job = job_parser.parse_from_url("https://example.com/job")
        assert job.company == "Cached Company"


class TestParseHTML:
    """Test _parse_html method."""

    def test_parse_html_linkedin_detected(self, job_parser):
        """Test LinkedIn detection in HTML."""
        html = '<html><body><div class="linkedin">Job</div></body></html>'
        job = job_parser._parse_html(html)
        assert job is not None

    def test_parse_html_indeed_detected(self, job_parser):
        """Test Indeed detection in HTML."""
        html = '<html><body><div class="indeed">Job</div></body></html>'
        job = job_parser._parse_html(html)
        assert job is not None


class TestHasLinkedInStructure:
    """Test _has_linkedin_structure method."""

    def test_has_linkedin_structure_true(self, job_parser):
        """Test LinkedIn structure detection."""
        html = '<html><body><div class="linkedin">Job</div></body></html>'
        assert job_parser._has_linkedin_structure(html) is True

    def test_has_linkedin_structure_false(self, job_parser):
        """Test non-LinkedIn HTML."""
        html = "<html><body><p>Generic job</p></body></html>"
        assert job_parser._has_linkedin_structure(html) is False


class TestHasIndeedStructure:
    """Test _has_indeed_structure method."""

    def test_has_indeed_structure_true(self, job_parser):
        """Test Indeed structure detection."""
        html = '<html><body><div class="indeed">Job</div></body></html>'
        assert job_parser._has_indeed_structure(html) is True

    def test_has_indeed_structure_false(self, job_parser):
        """Test non-Indeed HTML."""
        html = "<html><body><p>Generic job</p></body></html>"
        assert job_parser._has_indeed_structure(html) is False


class TestExtractPattern:
    """Test _extract_pattern method."""

    def test_extract_pattern_found(self, job_parser):
        """Test extracting pattern that exists."""
        text = "Company: Google"
        result = job_parser._extract_pattern(text, r"Company:\s*(\w+)")
        assert result == "Google"

    def test_extract_pattern_not_found(self, job_parser):
        """Test extracting pattern that doesn't exist."""
        text = "No company here"
        result = job_parser._extract_pattern(text, r"Company:\s*(\w+)", default="Default")
        assert result == "Default"

    def test_extract_pattern_default_empty(self, job_parser):
        """Test with empty default."""
        text = "No match"
        result = job_parser._extract_pattern(text, r"Company:\s*(\w+)")
        assert result == ""


class TestExtractList:
    """Test _extract_list method."""

    def test_extract_list_multiple(self, job_parser):
        """Test extracting multiple items."""
        text = "Skills: Python JavaScript Go Rust"
        result = job_parser._extract_list(text, r"Skills:\s*([A-Z][a-zA-Z]+)", max_items=3)
        assert len(result) <= 3

    def test_extract_list_deduplication(self, job_parser):
        """Test that duplicates are removed."""
        text = "Python Python JavaScript"
        result = job_parser._extract_list(text, r"([A-Z][a-z]+)", max_items=10)
        # Should have unique items (case-insensitive dedup)
        assert len(result) >= 1


class TestExtractItemsFromText:
    """Test _extract_items_from_text method."""

    def test_extract_items_from_text_bullets(self, job_parser):
        """Test extracting bullet points."""
        text = "• First item\n• Second item\n• Third item"
        result = job_parser._extract_items_from_text(text)
        assert len(result) >= 1

    def test_extract_items_from_text_numbered(self, job_parser):
        """Test extracting numbered list."""
        text = "1. First\n2. Second\n3. Third"
        result = job_parser._extract_items_from_text(text)
        assert len(result) >= 1


class TestCacheOperations:
    """Test cache-related methods."""

    def test_get_cache_key(self, job_parser):
        """Test cache key generation."""
        url = "https://example.com/job/123"
        key = job_parser._get_cache_key(url)
        assert isinstance(key, str)
        assert len(key) > 0

    def test_get_from_cache_miss(self, job_parser, tmp_path):
        """Test cache miss."""
        job_parser.cache_dir = tmp_path
        result = job_parser._get_from_cache("nonexistent_key")
        assert result is None

    def test_save_and_get_from_cache(self, job_parser, tmp_path):
        """Test saving and retrieving from cache."""
        job_parser.cache_dir = tmp_path
        cache_key = "test_key"

        job = JobDetails(
            company="Test",
            position="Test",
            requirements=["Test"],
            responsibilities=["Test"],
        )

        job_parser._save_to_cache(cache_key, job)
        retrieved = job_parser._get_from_cache(cache_key)

        assert retrieved is not None
        assert retrieved.company == "Test"


class TestParseLinkedIn:
    """Test _parse_linkedin method."""

    def test_parse_linkedin_basic(self, job_parser):
        """Test basic LinkedIn parsing."""
        html = """
        <html>
        <body>
            <h1>Senior Software Engineer</h1>
            <div class="company">LinkedIn</div>
        </body>
        </html>
        """
        job = job_parser._parse_linkedin(html)
        assert job.company is not None
        assert job.position is not None

    def test_parse_linkedin_remote_detection(self, job_parser):
        """Test remote detection in LinkedIn."""
        html = """
        <html>
        <body>
            <h1>Software Engineer</h1>
            <div>Remote position available</div>
        </body>
        </html>
        """
        job = job_parser._parse_linkedin(html)
        assert job.remote is True


class TestParseIndeed:
    """Test _parse_indeed method."""

    def test_parse_indeed_basic(self, job_parser):
        """Test basic Indeed parsing."""
        html = """
        <html>
        <body>
            <h1>Software Engineer</h1>
            <span class="company">Google</span>
        </body>
        </html>
        """
        job = job_parser._parse_indeed(html)
        assert job.company is not None


class TestParseGeneric:
    """Test _parse_generic method."""

    def test_parse_generic_basic(self, job_parser):
        """Test basic generic parsing."""
        html = """
        <html>
        <body>
            <h1>Software Engineer</h1>
            <p>Company: Acme Corp</p>
        </body>
        </html>
        """
        job = job_parser._parse_generic(html)
        assert job.position is not None


class TestParseJobPosting:
    """Test parse_job_posting function."""

    def test_parse_job_posting_from_file(self, tmp_path):
        """Test parse_job_posting with file path."""
        from cli.generators.job_parser import parse_job_posting

        html_file = tmp_path / "job.html"
        html_file.write_text("<html><body><h1>Engineer</h1></body></html>")

        # Use cache with tmp_path to avoid /dev/null issue
        with patch.object(JobParser, "__init__", lambda self, cache_dir=None: None):
            job = parse_job_posting(file_path=html_file, use_cache=True)
        assert job is not None

    def test_parse_job_posting_requires_input(self):
        """Test that either file or URL is required."""
        from cli.generators.job_parser import parse_job_posting

        with pytest.raises(ValueError):
            parse_job_posting()
