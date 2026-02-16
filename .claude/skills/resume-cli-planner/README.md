# Resume CLI Parallel Issues Planner

A project-specific skill for analyzing and planning parallel development work on Resume CLI GitHub issues.

## What This Does

This skill helps you:
1. **Analyze** all open GitHub issues for the Resume CLI project
2. **Prioritize** issues based on labels (priority, category, size)
3. **Group** issues into parallelizable work tracks
4. **Generate** git worktree commands for isolated development
5. **Plan** execution across multiple contributors or agents

## Usage

### Basic Usage

```bash
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py
```

### Filter by Category

```bash
# Focus on AI features
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --category ai

# Focus on testing
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --category testing

# Focus on ATS optimization
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --category ats
```

### Filter by Priority

```bash
# Only high-priority issues
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --priority high

# Only medium-priority issues
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --priority medium
```

### Filter by Size

```bash
# Quick wins (small tasks)
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --size small

# Medium complexity features
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --size medium
```

### Combine Filters

```bash
# High-priority AI features
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --category ai --priority high

# Medium-priority testing work
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --category testing --priority medium
```

### Control Parallelism

```bash
# Work on 2 parallel tracks
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --max-parallel 2

# Work on 6 parallel tracks
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --max-parallel 6
```

## Output

The planner outputs:

1. **Parallel Work Plan** - Shows top issues grouped by track (AI, ATS, Integration, Testing, etc.)
2. **Git Worktree Commands** - Ready-to-run commands for setting up isolated worktrees
3. **Sub-Agent Commands** - Instructions for launching parallel Claude Code agents
4. **Execution Summary** - Statistics about issues and tracks

## Example Workflow

### 1. Run the Planner

```bash
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --max-parallel 3
```

### 2. Create Worktrees

```bash
# Copy and run the worktree commands from the output
git worktree add ../feature-issue-24-add-ai-generated-interview -b feature/issue-24
git worktree add ../feature-issue-15-add-ats-score-checker -b feature/issue-15
git worktree add ../feature-issue-7-add-comprehensive-test -b feature/issue-7
```

### 3. Work on Issues

For each worktree, you can either:
- Work on it yourself
- Launch a sub-agent using Claude Code's Task tool
- Assign to another contributor

### 4. Complete and Create PR

```bash
# Navigate to worktree
cd ../feature-issue-24

# Push the branch
git push origin feature/issue-24

# Create PR linked to issue
gh pr create --title "Fix #24: Add AI-generated interview questions based on job description" \
  --body "Closes #24" \
  --base main

# Clean up worktree (optional)
cd ../resume-cli
git worktree remove ../feature-issue-24
```

## Issue Labels

The planner uses these GitHub labels:

### Priority
- `priority-high` (150 points) - Core features, user-facing improvements
- `priority-medium` (100 points) - Useful features, infrastructure
- `priority-low` (50 points) - Nice-to-have enhancements

### Category
- `category-ai` - AI-powered features
- `category-ats` - ATS optimization
- `category-integration` - External service integrations
- `category-testing` - Test coverage and CI/CD
- `category-ux` - User experience improvements
- `category-ui` - User interface (web, desktop)
- `category-enterprise` - Enterprise features
- `category-mobile` - Mobile app
- `category-templates` - Resume templates
- `category-analytics` - Tracking and analytics

### Size
- `size-small` - 1-2 hours
- `size-medium` - 4-8 hours
- `size-large` - 1-3 days
- `size-xl` - 1-2 weeks

### Type
- `enhancement` - New feature or improvement
- `documentation` - Documentation update
- `bug` - Bug fix (if applicable)

## Parallelization Guidelines

### CAN Work in Parallel
- Different categories (AI vs ATS vs Testing vs UX)
- Different code modules (cli/generators/ vs cli/integrations/)
- Independent features with no dependencies
- Different components (CLI commands vs API server vs templates)

### CANNOT Work in Parallel
- Issues modifying the same files
- Issues with explicit dependencies
- Coordinated schema changes (resume.yaml structure)
- Shared configuration changes

## Requirements

- GitHub CLI (`gh`) installed and authenticated
- Python 3.6+
- Git worktree support (Git 2.5+)

## Troubleshooting

### "Error fetching issues"
Make sure `gh` CLI is installed and authenticated:
```bash
gh auth login
```

### "No open issues found"
All issues may be closed, or there's a problem with the GitHub CLI.

### Worktree Already Exists
Remove existing worktree first:
```bash
git worktree remove ../feature-issue-XXX
```

## File Structure

```
.claude/skills/resume-cli-planner/
├── README.md                      # This file
├── skill.md                       # Skill documentation
└── scripts/
    └── resume_planner.py          # Main planner script
```

## Contributing

To improve this skill:
1. Add new category mappings in `resume_planner.py`
2. Adjust priority scores based on project needs
3. Improve parallelization logic
4. Add more filtering options
