# Resume CLI Parallel Issues Planner

Analyzes all open GitHub issues for the Resume CLI project, prioritizes them based on labels and categories, and creates an execution plan for parallel development using git worktrees and sub-agents.

## Quick Start

```bash
# Run the planner script
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py [OPTIONS]
```

**Options:**
- `--max-parallel N`: Maximum number of parallel worktrees (default: 4)
- `--category CAT`: Filter by category (ai, ats, integration, testing, ux, ui, enterprise, mobile, templates)
- `--priority P`: Filter by priority (high, medium, low)
- `--size S`: Filter by size (small, medium, large, xl)

## How It Works

The bundled `resume_planner.py` script:

1. **Fetches Issues**: Uses `gh` CLI to get all open issues with metadata
2. **Parses Labels**: Extracts priority, category, and size from issue labels
3. **Groups by Area**: Clusters issues into parallelizable tracks (AI, ATS, Integration, Testing, UX, UI, etc.)
4. **Calculates Priority Score**: Priority × Category matrix to rank issues
5. **Generates Plan**: Outputs worktree commands and execution plan

## Execution Workflow

### Step 1: Run the Planner

```bash
python3 .claude/skills/resume-cli-planner/scripts/resume_planner.py --max-parallel 4
```

The script outputs:
- Parallel tracks grouped by category area
- Priority score for each issue
- Git worktree setup commands
- Agent launch instructions

### Step 2: Create Git Worktrees

Copy and run the worktree commands from the output:

```bash
# Example output from planner
git worktree add ../feature-issue-24-add-ai-generated-interview -b feature/issue-24
git worktree add ../feature-issue-15-add-ats-score-checker -b feature/issue-15
git worktree add ../feature-issue-7-add-comprehensive-test -b feature/issue-7
git worktree add ../feature-issue-9-improve-error-messages -b feature/issue-9
```

### Step 3: Launch Parallel Agents

For each worktree, use the Task tool to launch background agents:

```
# Each agent works independently in its own worktree
# Monitor progress with TaskOutput
```

### Step 4: Monitor and Create PRs

When an agent completes work:

```bash
# Navigate to the worktree
cd ../feature-issue-24

# Push the branch
git push origin feature/issue-24

# Create PR linked to issue
gh pr create --title "Fix #24: Add AI-generated interview questions based on job description" --body "Closes #24" --base main

# Remove worktree after PR creation
cd resume-cli
git worktree remove ../feature-issue-24
```

## Priority Matrix

Issues are prioritized based on:

1. **Critical Path**: Issues that improve core functionality and user experience
2. **User Value**: Features that directly help users get jobs
3. **Foundation**: Testing, documentation, and infrastructure that enables other work
4. **Enhancement**: Nice-to-have features that add value

**Priority Scores:**
- **HIGH** (150 pts): Core AI features, ATS optimization, user experience improvements
- **MEDIUM** (100 pts): Integrations, UI improvements, test coverage
- **LOW** (50 pts): Enterprise features, mobile apps, template marketplace

## Category Areas

Resume CLI issues are organized into these categories:

- **ai** - AI-powered features (interview prep, multi-language, video resume)
- **ats** - Applicant Tracking System optimization (keyword density, ATS score, formats)
- **integration** - External service integrations (LinkedIn, job parsers, salary data)
- **testing** - Test coverage and CI/CD
- **ux** - User experience improvements (error messages, progress indicators, diffs)
- **ui** - User interface (web UI, desktop app)
- **enterprise** - Enterprise features (white-label, recruiter dashboard, team collaboration)
- **mobile** - Mobile app development
- **templates** - Resume templates and custom template support
- **analytics** - Application tracking and analytics (dashboard, metrics, comparison tools)

## Parallel Workability

**Issues CAN be worked in parallel when:**
- Different categories/areas (ai vs ats vs testing vs ux)
- Different code modules (cli/generators/ vs cli/integrations/ vs cli/utils/)
- Independent features with no shared dependencies
- Different components (web UI vs CLI commands vs API server)

**Issues CANNOT be worked in parallel when:**
- Modify the same files
- Have dependency relationships (e.g., web UI depends on API server)
- Require coordinated schema changes
- Share state management or configuration
- Need synchronous integration

## Codebase Areas

Understanding the directory structure helps with parallelization:

```
cli/
├── main.py              # CLI entry point
├── commands/            # CLI commands (generate, apply, sync-github, init)
├── generators/          # Template & AI engines
│   ├── template.py      # Jinja2 rendering
│   ├── ai_generator.py  # AI customization
│   ├── cover_letter_generator.py
│   └── ai_judge.py
├── integrations/        # External services
│   ├── tracking.py      # CSV application tracking
│   └── github_sync.py   # GitHub project sync
├── utils/               # Core utilities
│   ├── yaml_parser.py   # ResumeYAML data access
│   ├── config.py        # Configuration
│   └── schema.py        # Schema validation
└── generators/          # Resume generation engines

api/                     # FastAPI server (REST API)
├── main.py
├── models.py
└── auth.py

templates/               # Jinja2 templates (resume_md.j2, cover_letter_md.j2, etc.)
config/                  # Configuration files
tests/                   # Test files (to be added)
```

## Label Format

Issues use these labels:

**Priority:**
- `priority-high`
- `priority-medium`
- `priority-low`

**Category:**
- `category-ai`
- `category-ats`
- `category-integration`
- `category-testing`
- `category-ux`
- `category-ui`
- `category-enterprise`
- `category-mobile`
- `category-templates`
- `category-analytics`

**Size:**
- `size-small`
- `size-medium`
- `size-large`
- `size-xl`

**Type:**
- `enhancement`
- `documentation`
- `bug` (if applicable)

## Example Output

```
================================================================================
RESUME CLI PARALLEL ISSUES EXECUTION PLAN
================================================================================

Total tracks: 4
Total issues to work: 36

────────────────────────────────────────────────────────────────────────────────
TRACK 1: AI
────────────────────────────────────────────────────────────────────────────────

  Issue #24: Add AI-generated interview questions based on job description
  └─ Priority: HIGH | Category: ai | Size: large | Score: 150
  └─ Worktree: ../feature-issue-24-add-ai-generated-interview
  └─ Branch: feature/issue-24

  Issue #31: Add multi-language resume generation
  └─ Priority: LOW | Category: ai | Size: large | Score: 50
  └─ Worktree: ../feature-issue-31-add-multi-language-resume
  └─ Branch: feature/issue-31

[... more issues ...]

================================================================================
GIT WORKTREE SETUP COMMANDS
================================================================================

git worktree add ../feature-issue-24-add-ai-generated-interview -b feature/issue-24
git worktree add ../feature-issue-15-add-ats-score-checker -b feature/issue-15
git worktree add ../feature-issue-7-add-comprehensive-test -b feature/issue-7
git worktree add ../feature-issue-9-improve-error-messages -b feature/issue-9

================================================================================
EXECUTION SUMMARY
================================================================================

All open issues by priority:
  HIGH: 10 issues
  MEDIUM: 15 issues
  LOW: 12 issues

Parallel tracks (4):
  ai: 5 issues (total priority score: 450)
  ats: 3 issues (total priority score: 300)
  testing: 2 issues (total priority score: 250)
  ux: 4 issues (total priority score: 350)
```

## Size-Based Estimation

- **size-small**: 1-2 hours (quick fixes, small enhancements)
- **size-medium**: 4-8 hours (moderate features)
- **size-large**: 1-3 days (complex features)
- **size-xl**: 1-2 weeks (major features, new platforms)

## Recommended Starting Points

For new contributors, start with:
1. **UX improvements** (priority-high, size-small/medium) - Quick wins, visible impact
2. **Testing** (priority-high, size-medium) - Foundation work, clear requirements

For experienced contributors:
1. **AI features** (priority-high, size-large) - Core differentiators
2. **ATS optimization** (priority-high, size-medium/large) - High user value

## Technical Debt

Address these incrementally:
- Test coverage (issues #7, #8, #2)
- CI/CD pipeline (issue #3)
- API documentation (issue #5)
- Docker improvements (issue #6)
