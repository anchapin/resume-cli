#!/usr/bin/env python3
"""
Integration tests for Job Parser (LinkedIn, Indeed).

Tests the job posting parser with realistic HTML samples from
LinkedIn, Indeed, and generic job boards.
"""

import json
import tempfile
from pathlib import Path

import pytest

from cli.integrations.job_parser import JobDetails, JobParser, parse_job_posting

# Sample LinkedIn job posting HTML
LINKEDIN_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Senior Backend Engineer at Tech Company | LinkedIn</title>
</head>
<body>
    <div class="job-details-jobs-unified-top-card">
        <h1 class="topcard-layout__title">Senior Backend Engineer</h1>
        <div class="company-name">
            <a data-test-company-name="Tech Company">Tech Company</a>
        </div>
        <div class="job-details-jobs-unified-top-card__location">
            <span>San Francisco, CA</span>
            <span class="topcard__flavor--bullet">(Remote)</span>
        </div>
        <div class="job-details-jobs-unified-top-card__salary">
            $150,000 - $200,000 per year
        </div>
    </div>
    <div class="job-details__main-content" data-test-job-description>
        <h2>About the Role</h2>
        <p>We are looking for a Senior Backend Engineer to join our growing team.</p>
        
        <h3>Requirements</h3>
        <ul>
            <li>5+ years of Python experience</li>
            <li>Experience with AWS cloud services</li>
            <li>Kubernetes deployment and management</li>
            <li>PostgreSQL database design and optimization</li>
            <li>RESTful API development</li>
            <li>Microservices architecture</li>
        </ul>
        
        <h3>Responsibilities</h3>
        <ul>
            <li>Design and implement scalable APIs</li>
            <li>Mentor junior engineers</li>
            <li>Participate in code reviews</li>
            <li>Collaborate with product team</li>
            <li>Optimize system performance</li>
        </ul>
        
        <h3>Benefits</h3>
        <ul>
            <li>Health, dental, and vision insurance</li>
            <li>401(k) matching</li>
            <li>Unlimited PTO</li>
        </ul>
    </div>
</body>
</html>
"""

# Sample Indeed job posting HTML
INDEED_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Software Engineer - Google - Indeed</title>
</head>
<body>
    <div class="jobsearch-JobInfoHeader">
        <h1 class="jobsearch-JobInfoHeader-title">Software Engineer</h1>
        <div class="jobsearch-InlineCompanyRating">
            <span data-company-name="Google">Google</span>
        </div>
        <div class="jobsearch-JobInfoHeader-subtitle">
            Mountain View, CA
        </div>
    </div>
    <div class="jobsearch-SalaryMessage" data-tn-element="salaryInfo">
        $180,000 - $250,000 a year
    </div>
    <div id="jobDescriptionText" data-tn-element="jobDescription">
        <p>Join our team as a Software Engineer.</p>
        
        <p><b>Requirements:</b></p>
        <ul>
            <li>Bachelor's degree in Computer Science or related field</li>
            <li>3+ years of software development experience</li>
            <li>Proficiency in Java, Python, or Go</li>
            <li>Experience with distributed systems</li>
            <li>Strong problem-solving skills</li>
        </ul>
        
        <p><b>Responsibilities:</b></p>
        <ul>
            <li>Develop and maintain large-scale systems</li>
            <li>Write clean, efficient code</li>
            <li>Collaborate with cross-functional teams</li>
            <li>Debug and resolve technical issues</li>
        </ul>
        
        <p><b>Benefits:</b></p>
        <ul>
            <li>Competitive salary and equity</li>
            <li>Comprehensive health coverage</li>
            <li>Free meals and snacks</li>
        </ul>
    </div>
</body>
</html>
"""

# Sample generic job posting HTML
GENERIC_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Full Stack Developer - StartupXYZ</title>
</head>
<body>
    <h1>Full Stack Developer</h1>
    <p>Company: StartupXYZ</p>
    <p>Location: New York, NY (Hybrid)</p>
    <p>Salary: $120,000 - $160,000 per year</p>
    
    <h2>Requirements</h2>
    <ul>
        <li>3+ years of JavaScript experience</li>
        <li>React and Node.js proficiency</li>
        <li>SQL and NoSQL databases</li>
        <li>Git version control</li>
    </ul>
    
    <h2>Responsibilities</h2>
    <ul>
        <li>Build and maintain web applications</li>
        <li>Work with design team on UI/UX</li>
        <li>Write unit and integration tests</li>
    </ul>
</body>
</html>
"""

# Sample remote job HTML
REMOTE_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1>Remote Python Developer</h1>
    <p>Company: RemoteFirst Inc</p>
    <p>Location: 100% Remote - Work from Home</p>
    
    <h2>About This Position</h2>
    <p>This is a fully remote position. We are a remote-first company.</p>
    
    <h2>Requirements</h2>
    <ul>
        <li>Python 3.8+</li>
        <li>Django or FastAPI</li>
        <li>PostgreSQL</li>
    </ul>
</body>
</html>
"""


class TestJobDetails:
    """Test JobDetails dataclass."""

    def test_creation_with_required_fields(self):
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

    def test_creation_with_all_fields(self):
        """Test creating JobDetails with all fields."""
        job = JobDetails(
            company="Test Company",
            position="Senior Engineer",
            requirements=["Python", "Go"],
            responsibilities=["Design systems", "Mentor team"],
            salary="$150,000 - $200,000",
            remote=True,
            location="San Francisco, CA",
            url="https://example.com/job/123",
            job_type="full-time",
            experience_level="senior",
            description="Job description text",
            benefits=["Health insurance", "401k"],
        )

        assert job.salary == "$150,000 - $200,000"
        assert job.remote is True
        assert job.job_type == "full-time"
        assert job.experience_level == "senior"
        assert len(job.benefits) == 2

    def test_to_dict(self):
        """Test converting JobDetails to dictionary."""
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
        assert data["requirements"] == ["Python"]

    def test_to_json(self):
        """Test converting JobDetails to JSON string."""
        job = JobDetails(
            company="Test Company",
            position="Engineer",
            requirements=["Python", "Go"],
            responsibilities=["Code"],
            salary="$100k",
        )

        json_str = job.to_json()
        data = json.loads(json_str)

        assert data["company"] == "Test Company"
        assert data["salary"] == "$100k"

    def test_from_dict(self):
        """Test creating JobDetails from dictionary."""
        data = {
            "company": "Test Company",
            "position": "Engineer",
            "requirements": ["Python"],
            "responsibilities": ["Code"],
            "salary": "$100k",
            "remote": True,
        }

        job = JobDetails.from_dict(data)

        assert job.company == "Test Company"
        assert job.remote is True


class TestJobParserInitialization:
    """Test JobParser initialization."""

    def test_init_default(self):
        """Test initialization with default cache directory."""
        parser = JobParser()
        assert parser.cache_dir is not None
        assert parser.cache_dir.exists()

    def test_init_with_custom_cache_dir(self, tmp_path):
        """Test initialization with custom cache directory."""
        custom_cache = tmp_path / "custom_cache"
        parser = JobParser(cache_dir=custom_cache)
        assert parser.cache_dir == custom_cache

    def test_cache_dir_created_if_not_exists(self, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        JobParser(cache_dir=cache_dir)
        assert cache_dir.exists()


class TestParseFromFileLinkedIn:
    """Test parsing LinkedIn job postings from file."""

    def test_parse_linkedin_company(self, tmp_path):
        """Test extracting company from LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "Tech Company" in job.company

    def test_parse_linkedin_position(self, tmp_path):
        """Test extracting position from LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "Senior Backend Engineer" in job.position

    def test_parse_linkedin_salary(self, tmp_path):
        """Test extracting salary from LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.salary is not None
        assert "$150" in job.salary or "200" in job.salary

    def test_parse_linkedin_remote_detection(self, tmp_path):
        """Test remote detection in LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.remote is True

    def test_parse_linkedin_requirements(self, tmp_path):
        """Test extracting requirements from LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert len(job.requirements) > 0
        assert any("Python" in req for req in job.requirements)

    def test_parse_linkedin_responsibilities(self, tmp_path):
        """Test extracting responsibilities from LinkedIn HTML."""
        html_file = tmp_path / "linkedin_job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert len(job.responsibilities) > 0


class TestParseFromFileIndeed:
    """Test parsing Indeed job postings from file."""

    def test_parse_indeed_company(self, tmp_path):
        """Test extracting company from Indeed HTML."""
        html_file = tmp_path / "indeed_job.html"
        html_file.write_text(INDEED_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "Google" in job.company

    def test_parse_indeed_position(self, tmp_path):
        """Test extracting position from Indeed HTML."""
        html_file = tmp_path / "indeed_job.html"
        html_file.write_text(INDEED_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "Software Engineer" in job.position

    def test_parse_indeed_salary(self, tmp_path):
        """Test extracting salary from Indeed HTML."""
        html_file = tmp_path / "indeed_job.html"
        html_file.write_text(INDEED_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.salary is not None
        assert "$180" in job.salary or "250" in job.salary

    def test_parse_indeed_requirements(self, tmp_path):
        """Test extracting requirements from Indeed HTML."""
        html_file = tmp_path / "indeed_job.html"
        html_file.write_text(INDEED_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert len(job.requirements) > 0


class TestParseFromFileGeneric:
    """Test parsing generic job postings from file."""

    def test_parse_generic_company(self, tmp_path):
        """Test extracting company from generic HTML."""
        html_file = tmp_path / "generic_job.html"
        html_file.write_text(GENERIC_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "StartupXYZ" in job.company

    def test_parse_generic_position(self, tmp_path):
        """Test extracting position from generic HTML."""
        html_file = tmp_path / "generic_job.html"
        html_file.write_text(GENERIC_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert "Full Stack Developer" in job.position

    def test_parse_generic_requirements(self, tmp_path):
        """Test extracting requirements from generic HTML."""
        html_file = tmp_path / "generic_job.html"
        html_file.write_text(GENERIC_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert len(job.requirements) > 0
        assert any("JavaScript" in req for req in job.requirements)


class TestRemoteDetection:
    """Test remote job detection."""

    def test_remote_detection_remote_keyword(self, tmp_path):
        """Test detecting remote jobs with 'remote' keyword."""
        html_file = tmp_path / "remote_job.html"
        html_file.write_text(REMOTE_SAMPLE_HTML)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.remote is True

    def test_remote_detection_work_from_home(self, tmp_path):
        """Test detecting remote jobs with 'work from home' keyword."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Work from home position</p>
        </body>
        </html>
        """
        html_file = tmp_path / "wfh_job.html"
        html_file.write_text(html)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.remote is True

    def test_remote_detection_fully_remote(self, tmp_path):
        """Test detecting remote jobs with 'fully remote' keyword."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>This is a fully remote position</p>
        </body>
        </html>
        """
        html_file = tmp_path / "fully_remote_job.html"
        html_file.write_text(html)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.remote is True

    def test_remote_detection_hybrid(self, tmp_path):
        """Test detecting hybrid jobs."""
        html = """
        <html>
        <body>
            <h1>Developer</h1>
            <p>Hybrid work arrangement available</p>
        </body>
        </html>
        """
        html_file = tmp_path / "hybrid_job.html"
        html_file.write_text(html)

        parser = JobParser()
        job = parser.parse_from_file(html_file)

        assert job.remote is True  # Hybrid is considered remote-friendly


class TestCacheOperations:
    """Test cache operations."""

    def test_cache_save_and_retrieve(self, tmp_path):
        """Test saving and retrieving from cache."""
        parser = JobParser(cache_dir=tmp_path)
        cache_key = "test_key_123"

        job = JobDetails(
            company="Test Company",
            position="Test Position",
            requirements=["Skill 1"],
            responsibilities=["Task 1"],
            salary="$100k",
        )

        parser._save_to_cache(cache_key, job)
        retrieved = parser._get_from_cache(cache_key)

        assert retrieved is not None
        assert retrieved.company == "Test Company"
        assert retrieved.salary == "$100k"

    def test_cache_miss(self, tmp_path):
        """Test cache miss returns None."""
        parser = JobParser(cache_dir=tmp_path)
        result = parser._get_from_cache("nonexistent_key")
        assert result is None

    def test_clear_cache(self, tmp_path):
        """Test clearing cache."""
        parser = JobParser(cache_dir=tmp_path)

        # Add some cached items
        for i in range(3):
            job = JobDetails(
                company=f"Company {i}",
                position="Position",
                requirements=[],
                responsibilities=[],
            )
            parser._save_to_cache(f"key_{i}", job)

        cleared = parser.clear_cache()
        assert cleared == 3

    def test_url_caching(self, tmp_path):
        """Test that URL parsing uses cache."""
        parser = JobParser(cache_dir=tmp_path)
        url = "https://example.com/job/test"
        cache_key = parser._get_cache_key(url)

        # Pre-populate cache
        cached_job = JobDetails(
            company="Cached Company",
            position="Cached Position",
            requirements=["Cached Skill"],
            responsibilities=["Cached Task"],
        )
        parser._save_to_cache(cache_key, cached_job)

        # Should return cached data without making HTTP request
        job = parser.parse_from_url(url)
        assert job.company == "Cached Company"


class TestParseJobPostingFunction:
    """Test the parse_job_posting convenience function."""

    def test_parse_from_file(self, tmp_path):
        """Test parse_job_posting with file path."""
        html_file = tmp_path / "job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)

        job = parse_job_posting(file_path=html_file)

        assert job.company is not None
        assert job.position is not None

    def test_parse_from_file_with_output(self, tmp_path):
        """Test parse_job_posting with output file."""
        html_file = tmp_path / "job.html"
        html_file.write_text(LINKEDIN_SAMPLE_HTML)
        output_file = tmp_path / "output.json"

        job = parse_job_posting(file_path=html_file, output=output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["company"] == job.company

    def test_parse_requires_input(self):
        """Test that parse_job_posting requires file or URL."""
        with pytest.raises(ValueError, match="Either file_path or url must be provided"):
            parse_job_posting()

    def test_parse_with_cache_disabled(self, tmp_path):
        """Test parsing with cache disabled."""
        html_file = tmp_path / "job.html"
        html_file.write_text(GENERIC_SAMPLE_HTML)

        job = parse_job_posting(file_path=html_file, use_cache=False)

        assert job.company is not None


class TestSourceDetection:
    """Test automatic source detection."""

    def test_detect_linkedin_by_url(self):
        """Test LinkedIn detection by URL in HTML."""
        html = '<html><body><a href="https://linkedin.com/jobs/view/123">Job</a></body></html>'
        parser = JobParser()
        assert parser._is_linkedin(html) is True

    def test_detect_linkedin_by_structure(self):
        """Test LinkedIn detection by HTML structure."""
        html = '<html><body><div class="topcard-layout__title">Job</div></body></html>'
        parser = JobParser()
        assert parser._is_linkedin(html) is True

    def test_detect_indeed_by_url(self):
        """Test Indeed detection by URL in HTML."""
        html = '<html><body><a href="https://indeed.com/viewjob?jk=123">Job</a></body></html>'
        parser = JobParser()
        assert parser._is_indeed(html) is True

    def test_detect_indeed_by_structure(self):
        """Test Indeed detection by HTML structure."""
        html = '<html><body><div class="jobsearch-JobInfoHeader">Job</div></body></html>'
        parser = JobParser()
        assert parser._is_indeed(html) is True

    def test_generic_fallback(self):
        """Test generic parser as fallback."""
        html = "<html><body><h1>Job Title</h1><p>Company: Test</p></body></html>"
        parser = JobParser()
        assert parser._is_linkedin(html) is False
        assert parser._is_indeed(html) is False


class TestSalaryExtraction:
    """Test salary extraction patterns."""

    def test_salary_range_dollars(self):
        """Test extracting salary range with dollar signs."""
        html = "<p>Salary: $100,000 - $150,000 per year</p>"
        parser = JobParser()
        salary = parser._extract_salary_from_text(html)
        assert salary is not None
        assert "$100" in salary

    def test_salary_with_k_notation(self):
        """Test extracting salary with k notation."""
        html = "<p>Compensation: $150k - $200k</p>"
        parser = JobParser()
        salary = parser._extract_salary_from_text(html)
        assert salary is not None

    def test_salary_no_match(self):
        """Test when no salary is present."""
        html = "<p>Competitive salary offered</p>"
        parser = JobParser()
        salary = parser._extract_salary_from_text(html)
        assert salary is None


class TestExperienceLevelExtraction:
    """Test experience level extraction."""

    def test_extract_senior_level(self):
        """Test extracting senior level."""
        html = "<p>We're looking for a Senior Engineer</p>"
        parser = JobParser()
        level = parser._extract_experience_level(html)
        assert level == "senior"

    def test_extract_entry_level(self):
        """Test extracting entry level."""
        html = "<p>Entry-level position available</p>"
        parser = JobParser()
        level = parser._extract_experience_level(html)
        assert level == "entry-level"

    def test_extract_mid_level(self):
        """Test extracting mid level."""
        html = "<p>Mid-level developer needed</p>"
        parser = JobParser()
        level = parser._extract_experience_level(html)
        assert level == "mid-level"


class TestJobTypeExtraction:
    """Test job type extraction."""

    def test_extract_full_time(self):
        """Test extracting full-time."""
        html = "<p>Full-time position</p>"
        parser = JobParser()
        job_type = parser._extract_job_type(html)
        assert job_type == "full-time"

    def test_extract_part_time(self):
        """Test extracting part-time."""
        html = "<p>Part-time opportunity</p>"
        parser = JobParser()
        job_type = parser._extract_job_type(html)
        assert job_type == "part-time"

    def test_extract_contract(self):
        """Test extracting contract."""
        html = "<p>Contract role for 6 months</p>"
        parser = JobParser()
        job_type = parser._extract_job_type(html)
        assert job_type == "contract"


class TestIntegrationWithSampleFiles:
    """Integration tests with sample HTML files."""

    def test_parse_sample_linkedin(self):
        """Test parsing the sample LinkedIn job posting."""
        sample_path = Path(__file__).parent.parent / "sample_job_posting.html"
        if sample_path.exists():
            parser = JobParser()
            job = parser.parse_from_file(sample_path)

            assert job.company is not None
            assert job.position is not None

    def test_parse_sample_job_description(self):
        """Test parsing the sample job description text file."""
        sample_path = Path(__file__).parent.parent / "sample_job_description.txt"
        if sample_path.exists():
            # Convert text to simple HTML for parsing
            content = sample_path.read_text()
            html = f"<html><body>{content}</body></html>"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(html)
                temp_path = Path(f.name)

            try:
                parser = JobParser()
                job = parser.parse_from_file(temp_path)

                assert job.company is not None or job.position is not None
            finally:
                temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
