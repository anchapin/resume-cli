"""GitHub integration for syncing projects."""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class GitHubSync:
    """Sync GitHub projects to resume.yaml."""

    def __init__(self, config):
        """
        Initialize GitHub sync.

        Args:
            config: Config object with GitHub settings
        """
        self.config = config
        self.username = config.github_username

    def fetch_projects(self, months: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch recent projects from GitHub.

        Args:
            months: Number of months to look back

        Returns:
            Dictionary of projects by category
        """
        # Calculate date threshold
        date_threshold = self._calculate_date_threshold(months)

        # Fetch repos using gh CLI
        repos = self._fetch_repos(date_threshold)

        # Categorize repos
        categorized = self._categorize_repos(repos)

        return categorized

    def _calculate_date_threshold(self, months: int) -> str:
        """Calculate date threshold string."""
        import subprocess

        try:
            result = subprocess.run(
                ["date", f"-{months}months", "+%Y-%m-%d"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except:
            # Fallback to python
            from datetime import timedelta

            threshold = datetime.now() - timedelta(days=30 * months)
            return threshold.strftime("%Y-%m-%d")

    def _fetch_repos(self, date_threshold: str) -> List[Dict[str, Any]]:
        """Fetch repositories from GitHub using gh CLI."""
        # Use secure temp file instead of hardcoded /tmp path
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        temp_path = Path(temp_file.name)

        try:
            # Run gh repo list
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "list",
                    self.username,
                    "--limit",
                    "100",
                    "--json",
                    "name,description,primaryLanguage,stargazerCount,forkCount,createdAt,updatedAt,url",
                    "--jq",
                    f'[.[] | select(.updatedAt >= "{date_threshold}")] | sort_by(.updatedAt) | reverse',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Save to temp file for debugging
            temp_file.write(result.stdout)
            temp_file.close()

            repos = json.loads(result.stdout)
            return repos

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to fetch GitHub repos: {e.stderr}\n"
                f"Make sure 'gh' CLI is installed and authenticated."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse GitHub response: {e}")

    def _categorize_repos(self, repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize repositories by type.

        Args:
            repos: List of repo dictionaries

        Returns:
            Dictionary with categories: ai_ml, fullstack, backend, devops, energy, tools
        """
        categories = {
            "ai_ml": [],
            "fullstack": [],
            "backend": [],
            "devops": [],
            "energy": [],
            "tools": [],
        }

        for repo in repos:
            name = repo.get("name", "")
            description = repo.get("description", "")
            language = repo.get("primaryLanguage", {}).get("name", "Python")

            # Combine for searching
            search_text = f"{name} {description} {language}".lower()

            # Categorize based on keywords
            if any(
                kw in search_text
                for kw in [
                    "ai",
                    "agent",
                    "llm",
                    "machine learning",
                    "ml",
                    "reinforcement",
                    "neural",
                    "pytorch",
                    "tensorflow",
                    "transformer",
                ]
            ):
                categories["ai_ml"].append(self._format_repo(repo))
            elif any(
                kw in search_text for kw in ["react", "vue", "angular", "frontend", "web", "ui"]
            ):
                categories["fullstack"].append(self._format_repo(repo))
            elif any(
                kw in search_text
                for kw in ["api", "server", "backend", "fastapi", "django", "flask"]
            ):
                categories["backend"].append(self._format_repo(repo))
            elif any(
                kw in search_text
                for kw in [
                    "devops",
                    "kubernetes",
                    "k8s",
                    "docker",
                    "helm",
                    "cicd",
                    "github actions",
                ]
            ):
                categories["devops"].append(self._format_repo(repo))
            elif any(
                kw in search_text
                for kw in ["energy", "thermal", "building", "openstudio", "bem", "hvac"]
            ):
                categories["energy"].append(self._format_repo(repo))
            else:
                categories["tools"].append(self._format_repo(repo))

        return categories

    def _format_repo(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Format repo dict for resume."""
        return {
            "name": repo.get("name", ""),
            "description": repo.get("description", "No description"),
            "url": repo.get("url", ""),
            "stars": repo.get("stargazerCount", 0),
            "language": repo.get("primaryLanguage", {}).get("name", "Unknown"),
            "updated": repo.get("updatedAt", "")[:10],  # YYYY-MM-DD
        }

    def _fetch_readme(self, repo_owner: str, repo_name: str) -> str:
        """
        Fetch README content for a repository.

        Args:
            repo_owner: Repository owner (username)
            repo_name: Repository name

        Returns:
            README text or empty string on failure
        """
        try:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{repo_owner}/{repo_name}",
                    "--json",
                    "readme",
                    "--jq",
                    ".readme",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse JSON output (json is already imported at module level)
            readme_data = json.loads(result.stdout)
            if readme_data:
                # Extract text from README (handle potential HTML formatting)
                readme_text = readme_data.replace("\n", " ").strip()
                # Truncate if too long
                if len(readme_text) > 2000:
                    readme_text = readme_text[:2000]
                return readme_text
            return ""

        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return ""

    def _fetch_repo_topics(self, repo_owner: str, repo_name: str) -> List[str]:
        """
        Fetch topics for a repository.

        Args:
            repo_owner: Repository owner (username)
            repo_name: Repository name

        Returns:
            List of topic names (lowercased)
        """
        try:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{repo_owner}/{repo_name}",
                    "--json",
                    "repositoryTopics",
                    "--jq",
                    ".repositoryTopics[].name",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse output (one topic per line)
            topics = [
                line.strip().lower() for line in result.stdout.strip().split("\n") if line.strip()
            ]
            return topics

        except subprocess.CalledProcessError:
            return []

    def _fetch_repos_with_details(
        self, date_threshold: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch repositories from GitHub with enhanced details (topics and README).
        Only includes public repositories that are not forks.

        Args:
            date_threshold: Date threshold string (YYYY-MM-DD)
            limit: Maximum number of repos to fetch

        Returns:
            List of repo dictionaries with enhanced metadata
        """
        try:
            # Run gh repo list with topics
            # --public: only public repositories
            # jq filter: exclude forks (.isFork == false)
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "list",
                    self.username,
                    "--public",
                    "--limit",
                    str(limit),
                    "--json",
                    "name,description,primaryLanguage,stargazerCount,forkCount,createdAt,updatedAt,url,owner,isFork",
                    "--jq",
                    f'[.[] | select(.updatedAt >= "{date_threshold}" and .isFork == false)] | sort_by(.updatedAt) | reverse',
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            repos = json.loads(result.stdout)

            # Enhance each repo with topics and README
            for repo in repos:
                owner = repo.get("owner", {}).get("login", self.username)
                name = repo.get("name", "")

                # Fetch topics
                topics = self._fetch_repo_topics(owner, name)
                repo["topics"] = topics

                # Fetch README (limit to avoid too many API calls)
                # Only fetch README for repos updated recently or with stars
                if repo.get("stargazerCount", 0) > 0 or repo.get("forkCount", 0) > 5:
                    readme = self._fetch_readme(owner, name)
                    repo["readme"] = readme
                else:
                    repo["readme"] = ""

            return repos

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to fetch GitHub repos: {e.stderr}\n"
                f"Make sure 'gh' CLI is installed and authenticated."
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse GitHub response: {e}")

    def _search_code_in_org(
        self, technologies: List[str], limit_per_tech: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for code within the user's organization matching the technologies.

        Uses GitHub code search with org: qualifier to find repositories that
        contain the target technologies in their code.

        Args:
            technologies: List of technology keywords (lowercased)
            limit_per_tech: Max repositories to find per technology

        Returns:
            Dictionary mapping repo names to their code match counts
            Format: {"repo_name": {"count": 5, "url": "...", "technologies": ["langchain", ...]}}
        """
        repo_matches = {}

        for tech in technologies:
            try:
                # Search for code in organization
                # Using gh api search/code endpoint
                query = f"org:{self.username} {tech}"
                result = subprocess.run(
                    [
                        "gh",
                        "api",
                        "-X",
                        "GET",
                        "search/code",
                        "-f",
                        f"q={query}",
                        "--jq",
                        ".items[:10] | .[] | {repository: .repository | {name, url, owner, owner: .owner.login}, path: .path}",
                        "--limit",
                        "100",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Parse results
                if result.stdout.strip():
                    try:
                        # gh api outputs JSONL (one JSON object per line)
                        for line in result.stdout.strip().split("\n"):
                            if not line.strip():
                                continue
                            try:
                                item = json.loads(line)
                                repo_name = item.get("repository", {}).get("name", "")
                                repo_url = item.get("repository", {}).get("url", "")

                                if repo_name:
                                    if repo_name not in repo_matches:
                                        repo_matches[repo_name] = {
                                            "count": 0,
                                            "url": repo_url,
                                            "technologies": set(),
                                        }

                                    repo_matches[repo_name]["count"] += 1
                                    repo_matches[repo_name]["technologies"].add(tech)
                            except json.JSONDecodeError:
                                continue
                    except Exception:
                        # If JSON parsing fails, try single JSON object
                        try:
                            items = json.loads(result.stdout)
                            if isinstance(items, list):
                                for item in items:
                                    repo_name = item.get("repository", {}).get("name", "")
                                    repo_url = item.get("repository", {}).get("url", "")

                                    if repo_name:
                                        if repo_name not in repo_matches:
                                            repo_matches[repo_name] = {
                                                "count": 0,
                                                "url": repo_url,
                                                "technologies": set(),
                                            }

                                        repo_matches[repo_name]["count"] += 1
                                        repo_matches[repo_name]["technologies"].add(tech)
                        except (json.JSONDecodeError, KeyError):
                            pass

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Code search may fail due to rate limits or other issues
                # Silently continue without code search results
                continue

        # Convert sets to lists for JSON serialization
        for repo_name in repo_matches:
            repo_matches[repo_name]["technologies"] = list(repo_matches[repo_name]["technologies"])

        return repo_matches

    def calculate_tech_match_score(
        self,
        repo: Dict[str, Any],
        technologies: List[str],
        code_matches: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Calculate a match score for a repo against the target technologies.

        Scoring hierarchy:
        - Code matches (from org code search): 5 points (strongest signal)
        - Primary language match: 3 points
        - Name/description/topics match: 2 points each
        - README match: 1 point

        IMPORTANT: Only ONE technology needs to match for a repo to be included.
        Multi-word technologies are split into individual words for flexible matching.

        Args:
            repo: Repository dictionary
            technologies: List of technology keywords (lowercased)
            code_matches: Optional dict of code search results from _search_code_in_org

        Returns:
            Match score (higher is better)
        """
        score = 0

        # Split multi-word technologies into individual words for better matching
        # e.g., "langchain expression language" -> ["langchain", "expression", "language"]
        tech_words = []
        for tech in technologies:
            tech_lower = tech.lower()
            # Keep the full phrase for exact matches
            tech_words.append(tech_lower)
            # Also add individual words for flexible matching
            words = tech_lower.split()
            if len(words) > 1:
                tech_words.extend(words)

        # Deduplicate while preserving order
        seen = set()
        unique_tech_words = []
        for word in tech_words:
            if word not in seen and word not in ("and", "or", "the", "for", "with", "from"):
                seen.add(word)
                unique_tech_words.append(word)

        tech_lower = unique_tech_words

        # Check code matches (5 points - strongest signal of actual usage)
        if code_matches:
            repo_name = repo.get("name", "")
            if repo_name in code_matches:
                match_data = code_matches[repo_name]
                # Each code match is strong evidence, but cap to avoid over-weighting
                code_score = min(match_data.get("count", 0) * 5, 15)
                score += code_score

        # Check primary language (3 points)
        language = repo.get("primaryLanguage", {}).get("name", "").lower()
        if language and language in tech_lower:
            score += 3

        # Check repository name (2 points per matching technology word)
        name = repo.get("name", "").lower()
        for tech in tech_lower:
            if tech in name:
                score += 2
                # Don't break - accumulate score for all matching technologies

        # Check description (2 points per matching technology word)
        description = repo.get("description", "").lower()
        for tech in tech_lower:
            if tech in description:
                score += 2
                # Don't break - accumulate score for all matching technologies

        # Check topics (2 points each, max 6 points)
        topics = repo.get("topics", [])
        for topic in topics:
            if topic in tech_lower:
                score += 2
                if score >= 6:  # Cap topics contribution
                    break

        # Check README (1 point per match, max 3 points)
        readme = repo.get("readme", "").lower()
        readme_matches = 0
        for tech in tech_lower:
            if tech in readme:
                readme_matches += 1
                if readme_matches >= 3:
                    break
        score += min(readme_matches, 3)

        return score

    def select_matching_projects(
        self, technologies: List[str], top_n: int = 3, months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Select top GitHub projects that match the target technologies.

        IMPORTANT: Only ONE technology needs to match for a repo to be included.
        Multi-word technologies (e.g., "langchain expression language") are split
        into individual words for flexible matching.

        Selection criteria:
        1. Best tech stack match (highest score)
        2. Most recently updated (within same score tier)

        Scoring includes code search results from the organization:
        - Code matches (org code search): 5 points per match (max 15)
        - Primary language match: 3 points
        - Name/description/topics match: 2 points each
        - README match: 1 point

        Args:
            technologies: List of technology keywords
            top_n: Number of projects to return
            months: Number of months to look back for repos

        Returns:
            List of formatted project dictionaries for resume
        """
        if not technologies:
            return []

        # Only use top 3 technologies for matching to be more selective
        # This prevents matching on too many keywords which results in
        # just selecting the 3 most recent repositories
        technologies = technologies[:3]

        # Step 1: Search for code in organization
        code_matches = self._search_code_in_org(technologies)

        # Step 2: Calculate date threshold
        date_threshold = self._calculate_date_threshold(months)

        # Step 3: Fetch repos with details (only public, non-fork repos)
        repos = self._fetch_repos_with_details(date_threshold)

        if not repos:
            return []

        # Step 4: Score each repo including code match data
        scored_repos = []
        for repo in repos:
            score = self.calculate_tech_match_score(repo, technologies, code_matches)
            if score > 0:  # Only include repos with some match
                repo["match_score"] = score
                scored_repos.append(repo)

        if not scored_repos:
            return []

        # Sort by score (desc), then by updated date (desc)
        scored_repos.sort(key=lambda r: (r["match_score"], r.get("updatedAt", "")), reverse=True)

        # Select top N
        top_repos = scored_repos[:top_n]

        # Format for resume
        formatted_projects = []
        for repo in top_repos:
            formatted_projects.append(
                {
                    "name": repo.get("name", ""),
                    "description": repo.get("description", "No description"),
                    "url": repo.get("url", ""),
                    "stars": repo.get("stargazerCount", 0),
                    "language": repo.get("primaryLanguage", {}).get("name", "Unknown"),
                    "match_score": repo.get("match_score", 0),
                }
            )

        return formatted_projects

    def update_resume_projects(
        self, projects: List[Dict[str, Any]], yaml_path: Path, category: str = "featured"
    ) -> None:
        """
        Update resume.yaml with selected projects.

        Args:
            projects: List of project dictionaries
            yaml_path: Path to resume.yaml
            category: Category to add projects to (default: "featured")
        """
        from ..utils.yaml_parser import ResumeYAML

        yaml_handler = ResumeYAML(yaml_path)
        data = yaml_handler.load()

        # Initialize projects section if not present
        if "projects" not in data:
            data["projects"] = {}

        # Add/update category with selected projects
        # Remove match_score before saving (not needed in resume)
        clean_projects = []
        for p in projects:
            clean_projects.append(
                {
                    "name": p["name"],
                    "description": p["description"],
                    "url": p["url"],
                    "stars": p["stars"],
                    "language": p["language"],
                }
            )

        data["projects"][category] = clean_projects

        # Save updated YAML
        yaml_handler.save(data)

    def update_resume_yaml(
        self, projects: Dict[str, List[Dict[str, Any]]], yaml_path: Path
    ) -> None:
        """
        Update resume.yaml with fetched projects.

        Args:
            projects: Categorized projects dictionary
            yaml_path: Path to resume.yaml
        """
        from ..utils.yaml_parser import ResumeYAML

        yaml_handler = ResumeYAML(yaml_path)
        data = yaml_handler.load()

        # Update projects section
        data["projects"] = {
            category: [
                {
                    "name": p["name"],
                    "description": p["description"],
                    "url": p["url"],
                    "stars": p["stars"],
                    "language": p["language"],
                }
                for p in project_list
            ]
            for category, project_list in projects.items()
        }

        # Save updated YAML
        yaml_handler.save(data)
