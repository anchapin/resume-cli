"""Unit tests for GitHubSync class."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.integrations.github_sync import GitHubSync
from cli.utils.config import Config


class TestGitHubSyncInitialization:
    """Test GitHubSync initialization."""

    def test_init_with_config(self, mock_config: Config):
        """Test initialization with config."""
        sync = GitHubSync(mock_config)

        assert sync.config == mock_config
        assert sync.username == mock_config.github_username


class TestCalculateDateThreshold:
    """Test _calculate_date_threshold method."""

    def test_calculate_date_threshold_months_3(self, mock_config: Config):
        """Test date threshold calculation for 3 months."""
        sync = GitHubSync(mock_config)
        threshold = sync._calculate_date_threshold(3)

        # Should be approximately 3 months ago
        threshold_date = datetime.strptime(threshold, "%Y-%m-%d")
        now = datetime.now()
        diff = (now - threshold_date).days

        # Should be roughly 90 days (3 months)
        assert 85 <= diff <= 95

    def test_calculate_date_threshold_months_12(self, mock_config: Config):
        """Test date threshold calculation for 12 months."""
        sync = GitHubSync(mock_config)
        threshold = sync._calculate_date_threshold(12)

        # Should be approximately 12 months ago
        threshold_date = datetime.strptime(threshold, "%Y-%m-%d")
        now = datetime.now()
        diff = (now - threshold_date).days

        # Should be roughly 365 days (12 months)
        assert 350 <= diff <= 380


class TestFormatRepo:
    """Test _format_repo method."""

    def test_format_repo(self, mock_config: Config):
        """Test repo formatting."""
        sync = GitHubSync(mock_config)

        repo_data = {
            "name": "test-repo",
            "description": "Test repository",
            "url": "https://github.com/user/test-repo",
            "stargazerCount": 10,
            "primaryLanguage": {"name": "Python"},
            "updatedAt": "2024-01-15T00:00:00Z",
        }

        formatted = sync._format_repo(repo_data)

        assert formatted["name"] == "test-repo"
        assert formatted["description"] == "Test repository"
        assert formatted["url"] == "https://github.com/user/test-repo"
        assert formatted["stars"] == 10
        assert formatted["language"] == "Python"
        assert formatted["updated"] == "2024-01-15"

    def test_format_repo_missing_fields(self, mock_config: Config):
        """Test repo formatting handles missing fields."""
        sync = GitHubSync(mock_config)

        repo_data = {
            "name": "minimal-repo",
            "description": "",
            "url": "https://github.com/user/minimal-repo",
        }

        formatted = sync._format_repo(repo_data)

        assert formatted["name"] == "minimal-repo"
        assert formatted["description"] == "No description"
        assert formatted["stars"] == 0
        assert formatted["language"] == "Unknown"


class TestCategorizeRepos:
    """Test _categorize_repos method."""

    def test_categorize_repos_ai_ml(self, mock_config: Config):
        """Test categorization of AI/ML repos."""
        sync = GitHubSync(mock_config)

        repos = [
            {
                "name": "ml-pipeline",
                "description": "Machine learning pipeline using TensorFlow",
                "primaryLanguage": {"name": "Python"},
            },
            {
                "name": "llm-agent",
                "description": "Large language model agent",
                "primaryLanguage": {"name": "Python"},
            },
        ]

        categories = sync._categorize_repos(repos)

        assert len(categories["ai_ml"]) == 2
        assert any(r["name"] == "ml-pipeline" for r in categories["ai_ml"])

    def test_categorize_repos_fullstack(self, mock_config: Config):
        """Test categorization of fullstack repos."""
        sync = GitHubSync(mock_config)

        repos = [
            {
                "name": "web-app",
                "description": "React frontend with Python backend",
                "primaryLanguage": {"name": "TypeScript"},
            },
            {
                "name": "vue-project",
                "description": "Vue.js application",
                "primaryLanguage": {"name": "JavaScript"},
            },
        ]

        categories = sync._categorize_repos(repos)

        assert len(categories["fullstack"]) == 2
        assert any(r["name"] == "web-app" for r in categories["fullstack"])

    def test_categorize_repos_backend(self, mock_config: Config):
        """Test categorization of backend repos."""
        sync = GitHubSync(mock_config)

        repos = [
            {
                "name": "api-server",
                "description": "FastAPI REST API server",
                "primaryLanguage": {"name": "Python"},
            },
            {
                "name": "flask-service",
                "description": "Flask microservice",
                "primaryLanguage": {"name": "Python"},
            },
        ]

        categories = sync._categorize_repos(repos)

        assert len(categories["backend"]) == 2
        assert any(r["name"] == "api-server" for r in categories["backend"])

    def test_categorize_repos_devops(self, mock_config: Config):
        """Test categorization of DevOps repos."""
        sync = GitHubSync(mock_config)

        repos = [
            {
                "name": "k8s-config",
                "description": "Kubernetes configuration files",
                "primaryLanguage": {"name": "YAML"},
            },
            {
                "name": "docker-setup",
                "description": "Docker container setup",
                "primaryLanguage": {"name": "Shell"},
            },
        ]

        categories = sync._categorize_repos(repos)

        assert len(categories["devops"]) == 2
        assert any(r["name"] == "k8s-config" for r in categories["devops"])

    def test_categorize_repos_tools_fallback(self, mock_config: Config):
        """Test uncategorized repos go to tools."""
        sync = GitHubSync(mock_config)

        repos = [
            {
                "name": "random-script",
                "description": "Random utility scripts",
                "primaryLanguage": {"name": "Bash"},
            },
            {
                "name": "helper-tool",
                "description": "Helper utility",
                "primaryLanguage": {"name": "Python"},
            },
        ]

        categories = sync._categorize_repos(repos)

        assert len(categories["tools"]) == 2


class TestCalculateTechMatchScore:
    """Test calculate_tech_match_score method."""

    def test_calculate_tech_match_score_no_match(self, mock_config: Config):
        """Test score calculation with no tech match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "random-project",
            "description": "A random project",
            "primaryLanguage": {"name": "Bash"},
            "topics": [],
        }

        score = sync.calculate_tech_match_score(repo, ["Python", "Django", "React"])

        assert score == 0

    def test_calculate_tech_match_score_language_match(self, mock_config: Config):
        """Test score calculation with language match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "python-app",
            "description": "Python application",
            "primaryLanguage": {"name": "Python"},
            "topics": [],
        }

        score = sync.calculate_tech_match_score(repo, ["Python", "Django"])

        # Language match = 3 points
        assert score == 3

    def test_calculate_tech_match_score_name_match(self, mock_config: Config):
        """Test score calculation with name match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "django-project",
            "description": "Django web app",
            "primaryLanguage": {"name": "Python"},
            "topics": [],
        }

        score = sync.calculate_tech_match_score(repo, ["Django", "Python"])

        # Name match = 2 points
        assert score == 2

    def test_calculate_tech_match_score_description_match(self, mock_config: Config):
        """Test score calculation with description match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "web-api",
            "description": "REST API using FastAPI",
            "primaryLanguage": {"name": "Python"},
            "topics": [],
        }

        score = sync.calculate_tech_match_score(repo, ["FastAPI", "Python"])

        # Description match = 2 points
        assert score >= 2

    def test_calculate_tech_match_score_topic_match(self, mock_config: Config):
        """Test score calculation with topic match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "api-service",
            "description": "API service",
            "primaryLanguage": {"name": "Python"},
            "topics": ["kubernetes", "docker"],
        }

        score = sync.calculate_tech_match_score(repo, ["Kubernetes", "Docker"])

        # Topic match = 2 points per topic
        assert score >= 4  # At least 2 topics match

    def test_calculate_tech_match_score_code_match(self, mock_config: Config):
        """Test score calculation with code match."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "test-repo",
            "description": "Test",
            "primaryLanguage": {"name": "Python"},
            "topics": [],
        }

        code_matches = {"test-repo": {"count": 3, "url": "https://github.com/user/test-repo"}}

        score = sync.calculate_tech_match_score(repo, ["Python"], code_matches=code_matches)

        # Code match = 5 points per match, capped at 15
        # 3 matches * 5 = 15 (capped)
        assert score == 15

    def test_calculate_tech_match_score_case_insensitive(self, mock_config: Config):
        """Test score calculation is case-insensitive."""
        sync = GitHubSync(mock_config)

        repo = {
            "name": "k8s-deployment",
            "description": "Kubernetes deployment scripts",
            "primaryLanguage": {"name": "YAML"},
            "topics": [],
        }

        # Use uppercase in technologies
        score = sync.calculate_tech_match_score(repo, ["KUBERNETES", "DOCKER"])

        assert score > 0  # Should match despite case difference


class TestSelectMatchingProjects:
    """Test select_matching_projects method."""

    @patch("cli.integrations.github_sync.GitHubSync._search_code_in_org")
    @patch("cli.integrations.github_sync.GitHubSync._fetch_repos_with_details")
    def test_select_matching_projects_no_technologies(
        self, mock_fetch, mock_search, mock_config: Config
    ):
        """Test select returns empty when no technologies provided."""
        sync = GitHubSync(mock_config)

        result = sync.select_matching_projects([])

        assert result == []
        mock_fetch.assert_not_called()
        mock_search.assert_not_called()

    @patch("cli.integrations.github_sync.GitHubSync._search_code_in_org")
    @patch("cli.integrations.github_sync.GitHubSync._fetch_repos_with_details")
    def test_select_matching_projects_filters_and_sorts(
        self, mock_fetch, mock_search, mock_config: Config
    ):
        """Test select filters by match and sorts by score."""
        sync = GitHubSync(mock_config)

        # Mock repos with different match potential
        mock_fetch.return_value = {
            "high-match": {"count": 3, "url": "url1"},
            "medium-match": {"count": 1, "url": "url2"},
        }

        mock_fetch.return_value = [
            {
                "name": "high-match",
                "description": "Python Django project",
                "primaryLanguage": {"name": "Python"},
                "stargazerCount": 10,
                "url": "url1",
                "topics": ["django", "python"],
            },
            {
                "name": "medium-match",
                "description": "Some project",
                "primaryLanguage": {"name": "Java"},
                "stargazerCount": 5,
                "url": "url2",
                "topics": ["java"],
            },
            {
                "name": "no-match",
                "description": "Unrelated project",
                "primaryLanguage": {"name": "Bash"},
                "stargazerCount": 2,
                "url": "url3",
                "topics": ["bash"],
            },
        ]

        result = sync.select_matching_projects(technologies=["Python", "Django"], top_n=2)

        # Should return top 2 matching repos (sorted by score)
        assert len(result) <= 2
        assert any(r["name"] == "high-match" for r in result)

    @patch("cli.integrations.github_sync.GitHubSync._search_code_in_org")
    @patch("cli.integrations.github_sync.GitHubSync._fetch_repos_with_details")
    def test_select_matching_projects_excludes_zero_score(
        self, mock_fetch, mock_search, mock_config: Config
    ):
        """Test select excludes repos with zero match score."""
        sync = GitHubSync(mock_config)

        mock_fetch.return_value = {}
        mock_fetch.return_value = [
            {
                "name": "matched",
                "description": "Python project",
                "primaryLanguage": {"name": "Python"},
                "url": "url1",
                "topics": ["python"],
            },
            {
                "name": "no-match",
                "description": "Unrelated",
                "primaryLanguage": {"name": "Bash"},
                "url": "url2",
                "topics": ["bash"],
            },
        ]

        result = sync.select_matching_projects(technologies=["Python"], top_n=10)

        # Should only include matched repo
        assert len(result) == 1
        assert result[0]["name"] == "matched"

    @patch("cli.integrations.github_sync.GitHubSync._search_code_in_org")
    @patch("cli.integrations.github_sync.GitHubSync._fetch_repos_with_details")
    def test_select_matching_projects_formats_output(
        self, mock_fetch, mock_search, mock_config: Config
    ):
        """Test select formats output correctly."""
        sync = GitHubSync(mock_config)

        mock_fetch.return_value = {"repo": {"count": 1, "url": "url"}}
        mock_fetch.return_value = [
            {
                "name": "test-repo",
                "description": "Test description",
                "primaryLanguage": {"name": "Python"},
                "stargazerCount": 5,
                "url": "https://github.com/user/test-repo",
                "topics": ["python"],
                "match_score": 8,
            }
        ]

        result = sync.select_matching_projects(technologies=["Python"])

        assert len(result) == 1
        assert result[0]["name"] == "test-repo"
        assert result[0]["description"] == "Test description"
        assert result[0]["url"] == "https://github.com/user/test-repo"
        assert result[0]["stars"] == 5
        assert result[0]["language"] == "Python"
        assert "match_score" not in result[0]  # Should be cleaned


class TestUpdateResumeProjects:
    """Test update_resume_projects method."""

    @patch("cli.integrations.github_sync.GitHubSync")
    def test_update_resume_projects(self, mock_resume_class, mock_config: Config, temp_dir: Path):
        """Test update_resume_projects writes to YAML."""
        sync = GitHubSync(mock_config)

        yaml_path = temp_dir / "resume.yaml"

        # Mock ResumeYAML instance
        mock_handler = MagicMock()
        mock_resume_class.return_value = mock_handler
        mock_handler.load.return_value = {"meta": {"version": "1.0"}}

        projects = [
            {
                "name": "project1",
                "description": "Description 1",
                "url": "url1",
                "stars": 10,
                "language": "Python",
                "match_score": 8,
            }
        ]

        sync.update_resume_projects(projects, yaml_path)

        # Verify load and save were called
        mock_handler.load.assert_called_once()
        mock_handler.save.assert_called_once()

        # Verify saved data structure
        saved_data = mock_handler.save.call_args[0][0][0]
        assert "projects" in saved_data
        assert saved_data["projects"]["featured"][0]["name"] == "project1"
        # match_score should be removed
        assert "match_score" not in saved_data["projects"]["featured"][0]


class TestFetchReposWithDetails:
    """Test _fetch_repos_with_details method."""

    @patch("subprocess.run")
    def test_fetch_repos_with_details_success(self, mock_run, mock_config: Config):
        """Test fetching repos with details succeeds."""
        sync = GitHubSync(mock_config)

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "name": "test-repo",
                        "description": "Test",
                        "primaryLanguage": {"name": "Python"},
                        "stargazerCount": 5,
                        "forkCount": 2,
                        "url": "https://github.com/user/test-repo",
                        "owner": {"login": "user"},
                        "isFork": False,
                        "updatedAt": "2024-01-15T00:00:00Z",
                    }
                ]
            ),
            stderr="",
        )

        repos = sync._fetch_repos_with_details(date_threshold="2023-01-01")

        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"

    @patch("subprocess.run")
    def test_fetch_repos_with_details_command_error(self, mock_run, mock_config: Config):
        """Test fetching handles subprocess error."""
        sync = GitHubSync(mock_config)

        mock_run.side_effect = RuntimeError("Command failed")

        with pytest.raises(RuntimeError) as exc_info:
            sync._fetch_repos_with_details(date_threshold="2023-01-01")

        assert "Failed to fetch GitHub repos" in str(exc_info.value)

    @patch("subprocess.run")
    def test_fetch_repos_with_details_json_error(self, mock_run, mock_config: Config):
        """Test fetching handles JSON decode error."""
        sync = GitHubSync(mock_config)

        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json", stderr="")

        with pytest.raises(RuntimeError) as exc_info:
            sync._fetch_repos_with_details(date_threshold="2023-01-01")

        assert "Failed to parse GitHub response" in str(exc_info.value)


class TestFetchReadme:
    """Test _fetch_readme method."""

    @patch("subprocess.run")
    def test_fetch_readme_success(self, mock_run, mock_config: Config):
        """Test fetching README succeeds."""
        sync = GitHubSync(mock_config)

        mock_run.return_value = MagicMock(
            returncode=0, stdout="README content with some text and more text", stderr=""
        )

        readme = sync._fetch_readme("user", "repo")

        assert "README content" in readme

    @patch("subprocess.run")
    def test_fetch_readme_error(self, mock_run, mock_config: Config):
        """Test fetching README returns empty string on error."""
        sync = GitHubSync(mock_config)

        mock_run.side_effect = RuntimeError("Command failed")

        readme = sync._fetch_readme("user", "repo")

        assert readme == ""

    @patch("subprocess.run")
    def test_fetch_readme_truncates_long(self, mock_run, mock_config: Config):
        """Test fetching README truncates long content."""
        sync = GitHubSync(mock_config)

        # Create a very long README
        long_readme = "A" * 3000
        mock_run.return_value = MagicMock(returncode=0, stdout=long_readme, stderr="")

        readme = sync._fetch_readme("user", "repo")

        # Should be truncated to ~2000 chars
        assert len(readme) <= 2005


class TestFetchRepoTopics:
    """Test _fetch_repo_topics method."""

    @patch("subprocess.run")
    def test_fetch_repo_topics_success(self, mock_run, mock_config: Config):
        """Test fetching topics succeeds."""
        sync = GitHubSync(mock_config)

        mock_run.return_value = MagicMock(
            returncode=0, stdout="python\ndjango\nrest-api", stderr=""
        )

        topics = sync._fetch_repo_topics("user", "repo")

        assert len(topics) == 3
        assert "python" in topics
        assert "django" in topics
        assert "rest-api" in topics

    @patch("subprocess.run")
    def test_fetch_repo_topics_error(self, mock_run, mock_config: Config):
        """Test fetching topics returns empty list on error."""
        sync = GitHubSync(mock_config)

        mock_run.side_effect = RuntimeError("Command failed")

        topics = sync._fetch_repo_topics("user", "repo")

        assert topics == []


class TestSearchCodeInOrg:
    """Test _search_code_in_org method."""

    @patch("subprocess.run")
    def test_search_code_in_org_success(self, mock_run, mock_config: Config):
        """Test code search succeeds."""
        sync = GitHubSync(mock_config)

        # Mock JSONL output (one JSON per line)
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"repository": {"name": "repo1", "url": "url1", "owner": {"login": "user"}}\n{"repository": {"name": "repo2", "url": "url2", "owner": {"login": "user"}}',
            stderr="",
        )

        results = sync._search_code_in_org(technologies=["Python", "Django"])

        assert "repo1" in results
        assert "repo2" in results
        assert results["repo1"]["count"] == 2  # Both techs match

    @patch("subprocess.run")
    def test_search_code_in_org_handles_timeout(self, mock_run, mock_config: Config):
        """Test code search handles timeout gracefully."""
        sync = GitHubSync(mock_config)

        mock_run.side_effect = TimeoutError("Timeout")

        results = sync._search_code_in_org(technologies=["Python"])

        # Should return empty on timeout/error
        assert results == {}
