#!/usr/bin/env python3
"""Resume CLI Parallel Issues Planner - Analyzes GitHub issues and creates parallel work plans."""

import json
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional


@dataclass
class Issue:
    """Represents a GitHub issue."""
    number: int
    title: str
    body: str
    labels: List[str]
    priority: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    issue_type: Optional[str] = None

    @property
    def priority_score(self) -> int:
        """Calculate priority score (higher = more important)."""
        priority_scores = {"high": 150, "medium": 100, "low": 50}

        # Base score from priority
        score = priority_scores.get(self.priority or "low", 0)

        # Bonus for documentation and testing (foundation work)
        if self.issue_type == "documentation" or self.category == "testing":
            score += 25

        return score

    @property
    def key_area(self) -> str:
        """Determine the key area for parallel work."""
        if self.category:
            return self.category

        # Extract from title/body for issues without category labels
        text = (self.title + " " + self.body).lower()

        # Area keywords mapping to Resume CLI codebase
        area_keywords = {
            "ai": ["ai", "interview", "claude", "openai", "gpt", "gemini", "multi-language", "video resume"],
            "ats": ["ats", "applicant tracking", "keyword", "density", "score", "parse", "docx", "plain text"],
            "integration": ["integration", "linkedin", "import", "export", "sync", "parser", "job posting", "salary"],
            "testing": ["test", "pytest", "coverage", "unit", "integration", "e2e", "ci/cd", "github actions"],
            "ux": ["ux", "user experience", "error message", "progress", "diff", "comparison", "actionable guidance"],
            "ui": ["ui", "web", "dashboard", "interface", "visual", "desktop", "electron", "tauri"],
            "enterprise": ["enterprise", "white-label", "recruiter", "team", "collaboration", "career coach"],
            "mobile": ["mobile", "ios", "android", "responsive", "touch", "app"],
            "templates": ["template", "custom", "marketplace", "design"],
            "analytics": ["analytics", "metrics", "dashboard", "tracking", "offer comparison", "statistics"],
            "api": ["api", "fastapi", "rest", "swagger", "openapi", "endpoint"],
        }

        for area, keywords in area_keywords.items():
            if any(kw in text for kw in keywords):
                return area
        return "other"


def parse_issue_labels(labels: List[str]) -> tuple:
    """Parse priority, category, size, and type from issue labels."""
    priority = None
    category = None
    size = None
    issue_type = None

    for label in labels:
        label_lower = label.lower()

        # Priority
        if label_lower.startswith("priority-"):
            priority = label_lower.replace("priority-", "")
        # Category
        elif label_lower.startswith("category-"):
            category = label_lower.replace("category-", "")
        # Size
        elif label_lower.startswith("size-"):
            size = label_lower.replace("size-", "")
        # Type
        elif label_lower in ("enhancement", "documentation", "bug"):
            issue_type = label_lower

    return priority, category, size, issue_type


def fetch_issues(limit: int = 100) -> List[Issue]:
    """Fetch open issues from GitHub."""
    print("Fetching open issues from GitHub...")
    result = subprocess.run(
        ["gh", "issue", "list", "--limit", str(limit), "--state", "open",
         "--json", "number,title,body,labels"],
        capture_output=True,
        text=True,
        check=True
    )

    issues = []
    for item in json.loads(result.stdout):
        labels = [label["name"] for label in item.get("labels", [])]
        priority, category, size, issue_type = parse_issue_labels(labels)

        issues.append(Issue(
            number=item["number"],
            title=item["title"],
            body=item.get("body", ""),
            labels=labels,
            priority=priority,
            category=category,
            size=size,
            issue_type=issue_type
        ))

    print(f"Fetched {len(issues)} issues")
    return issues


def group_by_parallel_workability(issues: List[Issue], max_tracks: int = 4) -> Dict[str, List[Issue]]:
    """Group issues that can be worked on in parallel."""

    # Group by key area
    area_groups = defaultdict(list)
    for issue in issues:
        area = issue.key_area
        area_groups[area].append(issue)

    # Sort each group by priority
    for area in area_groups:
        area_groups[area].sort(key=lambda i: (-i.priority_score, i.number))

    # Select top tracks based on total priority score
    sorted_areas = sorted(
        area_groups.items(),
        key=lambda x: sum(i.priority_score for i in x[1]),
        reverse=True
    )

    tracks = {}
    for area, area_issues in sorted_areas[:max_tracks]:
        tracks[area] = area_issues

    return tracks


def generate_worktree_name(issue: Issue) -> str:
    """Generate a worktree directory name for an issue."""
    # Clean the title for use as directory name
    clean_title = re.sub(r'[^\w\s-]', '', issue.title)
    clean_title = re.sub(r'[-\s]+', '-', clean_title)
    clean_title = clean_title.strip('-').lower()[:50]
    return f"../feature-issue-{issue.number}-{clean_title}"


def generate_branch_name(issue: Issue) -> str:
    """Generate a branch name for an issue."""
    return f"feature/issue-{issue.number}"


def print_plan(tracks: Dict[str, List[Issue]], max_issues_per_track: int = 3):
    """Print the parallel work plan."""

    print("\n" + "=" * 80)
    print("RESUME CLI PARALLEL ISSUES EXECUTION PLAN")
    print("=" * 80)

    total_issues = sum(len(issues) for issues in tracks.values())
    print(f"\nTotal tracks: {len(tracks)}")
    print(f"Total issues to work: {total_issues}\n")

    for i, (area, issues) in enumerate(tracks.items(), 1):
        print(f"\n{'─' * 80}")
        print(f"TRACK {i}: {area.upper()}")
        print(f"{'─' * 80}")

        for issue in issues[:max_issues_per_track]:
            prio_str = issue.priority.upper() if issue.priority else "UNSET"
            size_str = f" | Size: {issue.size}" if issue.size else ""
            worktree = generate_worktree_name(issue)
            branch = generate_branch_name(issue)

            print(f"\n  Issue #{issue.number}: {issue.title}")
            print(f"  └─ Priority: {prio_str} | Category: {issue.category or area}{size_str} | Score: {issue.priority_score}")
            print(f"  └─ Worktree: {worktree}")
            print(f"  └─ Branch: {branch}")

    print("\n" + "=" * 80)


def print_git_commands(tracks: Dict[str, List[Issue]], max_issues_per_track: int = 1):
    """Print git commands to set up worktrees."""

    print("\n" + "=" * 80)
    print("GIT WORKTREE SETUP COMMANDS")
    print("=" * 80 + "\n")

    all_commands = []

    for area, issues in tracks.items():
        for issue in issues[:max_issues_per_track]:
            worktree = generate_worktree_name(issue)
            branch = generate_branch_name(issue)
            cmd = f"git worktree add {worktree} -b {branch}"
            all_commands.append((issue.number, issue.title[:40], cmd))

    for num, title, cmd in all_commands:
        print(f"# Issue #{num}: {title}")
        print(cmd)
        print()


def print_agent_commands(tracks: Dict[str, List[Issue]], max_issues_per_track: int = 1):
    """Print commands to launch parallel agents."""

    print("\n" + "=" * 80)
    print("SUB-AGENT LAUNCH COMMANDS (for Claude Code)")
    print("=" * 80 + "\n")

    print("# Run these commands in parallel to work on issues simultaneously\n")

    for area, issues in tracks.items():
        for issue in issues[:max_issues_per_track]:
            worktree = generate_worktree_name(issue)
            branch = generate_branch_name(issue)

            print(f"# Track: {area} | Issue #{issue.number}: {issue.title[:50]}")
            print(f"# cd {worktree} && # Work in this directory")
            print(f"# Read the issue and implement the feature")


def print_summary(tracks: Dict[str, List[Issue]], issues: List[Issue]):
    """Print execution summary."""

    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)

    # Count by priority
    priority_counts = defaultdict(int)
    for issue in issues:
        if issue.priority:
            priority_counts[issue.priority] += 1

    print(f"\nAll open issues by priority:")
    for priority in sorted(priority_counts.keys()):
        print(f"  {priority.upper()}: {priority_counts[priority]} issues")

    # Count by category
    category_counts = defaultdict(int)
    for issue in issues:
        if issue.category:
            category_counts[issue.category] += 1

    print(f"\nAll open issues by category:")
    for category in sorted(category_counts.keys()):
        print(f"  {category}: {category_counts[category]} issues")

    # Track summary
    print(f"\nParallel tracks ({len(tracks)}):")
    for area, area_issues in tracks.items():
        total_score = sum(i.priority_score for i in area_issues)
        print(f"  {area}: {len(area_issues)} issues (total priority score: {total_score})")

    print("\n" + "=" * 80)


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Parse arguments
    max_parallel = 4
    filter_category = None
    filter_priority = None
    filter_size = None

    i = 0
    while i < len(args):
        if args[i] == "--max-parallel" and i + 1 < len(args):
            max_parallel = int(args[i + 1])
            i += 2
        elif args[i] == "--category" and i + 1 < len(args):
            filter_category = args[i + 1].lower()
            i += 2
        elif args[i] == "--priority" and i + 1 < len(args):
            filter_priority = args[i + 1].lower()
            i += 2
        elif args[i] == "--size" and i + 1 < len(args):
            filter_size = args[i + 1].lower()
            i += 2
        else:
            i += 1

    # Fetch issues
    try:
        issues = fetch_issues()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching issues: {e}")
        print("Make sure 'gh' CLI is installed and authenticated.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error parsing GitHub response.")
        sys.exit(1)

    if not issues:
        print("No open issues found.")
        return

    # Filter if needed
    if filter_category:
        issues = [i for i in issues if i.category == filter_category]
        print(f"Filtered to category '{filter_category}': {len(issues)} issues")

    if filter_priority:
        issues = [i for i in issues if i.priority == filter_priority]
        print(f"Filtered to {filter_priority.upper()} priority: {len(issues)} issues")

    if filter_size:
        issues = [i for i in issues if i.size == filter_size]
        print(f"Filtered to {filter_size.upper()} size: {len(issues)} issues")

    if not issues:
        print("No issues match the filters.")
        return

    # Sort all issues by priority
    issues.sort(key=lambda i: (-i.priority_score, i.number))

    # Create parallel work plan
    tracks = group_by_parallel_workability(issues, max_tracks=max_parallel)

    # Print the plan
    print_plan(tracks, max_issues_per_track=3)
    print_git_commands(tracks, max_issues_per_track=1)
    print_agent_commands(tracks, max_issues_per_track=1)
    print_summary(tracks, issues)

    print("\nNext steps:")
    print("1. Create worktrees using the commands above")
    print("2. For each worktree, launch a sub-agent or work on the issue")
    print("3. When complete, push and create PR with: gh pr create --body 'Closes #<issue>'")
    print()


if __name__ == "__main__":
    main()
