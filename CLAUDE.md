# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Resume CLI System** - a unified command-line interface for generating job-specific resumes from a single YAML source. The system supports fast template-based generation (Jinja2) and optional AI-powered customization (Claude/OpenAI), with built-in application tracking.

**Key principle**: `resume.yaml` is the single source of truth. All resume variants are generated from this file.

## Development Commands

### Installation

```bash
# Standard installation
pip install -e .

# With AI support (adds anthropic/openai packages)
pip install -e ".[ai]"

# Development dependencies (includes pytest)
pip install -e ".[dev]"

# Set AI API key (if using AI features)
cp .env.template .env
# Edit .env to add your keys
# or set directly:
export ANTHROPIC_API_KEY=your_key_here
# or
export OPENAI_API_KEY=your_key_here
```

### Common Operations

```bash
# Validate resume.yaml schema
resume-cli validate

# Generate resume (template-based, <1 second)
resume-cli generate -v v1.0.0-base -f md
resume-cli generate -v v1.1.0-backend -f pdf

# List all variants
resume-cli variants

# Check ATS compatibility score
resume-cli ats-check -v v1.1.0-backend --job-desc job-posting.txt
resume-cli ats-check --job-desc job.txt --output ats-report.json

# Generate complete application package (resume + cover letter)
resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend
resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive
resume-cli generate-package --job-desc job.txt -f pdf --variant v1.2.0-ml_ai

# Generate package with auto-selected GitHub projects matching job technologies
resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend --include-github-projects

# Track job application
resume-cli apply Company applied -r "Job Title"

# View application analytics
resume-cli analyze

# Sync GitHub projects to resume.yaml
resume-cli sync-github --months 3
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cli --cov-report=html

# Run specific test file
pytest tests/test_yaml_parser.py
```

**Note**: As of the current version, the test suite is not yet implemented. The package is configured for pytest with the `dev` extra.

## Development Notes

### Adding New Commands

1. Create command function in `cli/main.py` or new file in `cli/commands/`
2. Use `@click.pass_context` decorator to access `ctx.obj` (contains `yaml_path`, `config`, `yaml_handler`)
3. Register with `@cli.command()` decorator
4. Example pattern:
```python
@cli.command()
@click.option("--example", type=str, help="Example option")
@click.pass_context
def my_command(ctx, example):
    """Command description."""
    yaml_handler = ctx.obj['yaml_handler']
    config = ctx.obj['config']
    # Your logic here
```

**Important**: The Click context object (`ctx.obj`) is initialized in the `@click.group()` decorator function `cli()` at the top of `cli/main.py`. All subcommands must use `@click.pass_context` to access this context.

### Adding New Template Formats

1. Create new Jinja2 template in `templates/` (e.g., `resume_html.j2`)
2. Add format to choice list in `generate` command in `cli/main.py`
3. Update `TemplateGenerator._get_template_extension()` if needed
4. Handle any special compilation in `TemplateGenerator.generate()`

### Modifying AI Prompts

AI prompts are defined in `cli/generators/ai_generator.py`. The system uses:
- Keyword extraction from job descriptions
- Bullet reordering based on relevance
- Skill highlighting
- **Important**: AI is configured to maintain truthfulness - no fake experience generated

## Architecture

### Data Flow

```
resume.yaml (single source)
    ↓
ResumeYAML parser (cli/utils/yaml_parser.py)
    ↓
TemplateGenerator (cli/generators/template.py)
    ↓
Jinja2 templates (templates/*.j2)
    ↓
Output files (output/)
```

For AI generation:
```
resume.yaml → TemplateGenerator → Base resume
                                    ↓
                            Job description
                                    ↓
                            AIGenerator → Customized resume
```

For cover letters with AI Judge:
```
Job description + resume.yaml → CoverLetterGenerator
                                    ↓
                            Generate N versions (configurable)
                                    ↓
                            AIJudge evaluates all versions
                                    ↓
                            Select and return best version
```

For generate-package with GitHub projects:
```
Job description → Extract technologies (AI)
                        ↓
                GitHubSync.select_matching_projects()
                        ↓
                Update resume.yaml with selected projects
                        ↓
                Generate AI-customized resume + cover letter
```

### Architectural Patterns

**Generator Pattern**: Both `TemplateGenerator`, `AIGenerator`, and `CoverLetterGenerator` implement a similar interface:
- Accept `yaml_path` and optional `config` in `__init__`
- Use `ResumeYAML` for data access
- Generate output in specified format (md/tex/pdf)
- Return generated content as string

**Context Object Pattern**: The Click CLI uses `ctx.obj` to share state across commands:
- Initialized in the `@click.group()` decorator function
- Contains `yaml_path` (Path), `config` (Config), `yaml_handler` (ResumeYAML)
- Accessed via `@click.pass_context` decorator in subcommands

**Config Layer Pattern**: Configuration is loaded with precedence:
1. Environment variables (.env file) - highest priority
2. config/default.yaml
3. Code defaults (`Config.DEFAULT_CONFIG` in cli/utils/config.py) - fallback
This allows flexible customization without code changes.

**Important env var overrides** (from .env file):
- `ANTHROPIC_API_KEY`: Required for Claude API access
- `ANTHROPIC_BASE_URL`: Optional custom API base URL (e.g., for z.ai or OpenRouter)
- `OPENAI_API_KEY`: Required for OpenAI GPT API access
- `OPENAI_BASE_URL`: Optional custom API base URL

### Key Components

**cli/utils/yaml_parser.py** (`ResumeYAML` class):
- Central data access layer for `resume.yaml`
- Methods: `get_contact()`, `get_summary(variant)`, `get_skills(variant)`, `get_experience(variant)`
- Variant-specific filtering uses `emphasize_for` lists in bullet items
- All variant data lives in `resume.yaml` under `variants:` key

**cli/generators/template.py** (`TemplateGenerator` class):
- Fast Jinja2-based rendering (<1 second)
- Supports MD, TEX formats (PDF via pdflatex/pandoc)
- Template context includes filtered data based on variant

**cli/generators/ai_generator.py** (`AIGenerator` class):
- Wraps `TemplateGenerator` for base resume
- Calls Claude/OpenAI API with job description
- Extracts keywords, reorders bullets, emphasizes matching experience
- Automatic fallback to template on API failure
- Supports AI Judge for multi-generation quality selection (configurable)

**cli/generators/cover_letter_generator.py** (`CoverLetterGenerator` class):
- Generates personalized cover letters using AI
- Interactive mode: asks questions (motivation, connections, etc.)
- Non-interactive mode: uses AI smart guesses
- Supports both Markdown and PDF output
- Extracts job details (company, position, requirements) from job description
- Uses AI Judge for multi-generation quality selection (configurable)

**cli/generators/ai_judge.py** (`AIJudge` class):
- Evaluates and selects best version from multiple AI generations
- Used by both resume and cover letter generators
- Configurable via `ai.judge_enabled` and `ai.num_generations` in config

**cli/main.py** (Click CLI):
- Entry point with `@click.group()` decorator
- Context object `ctx.obj` stores `yaml_path`, `config`, `yaml_handler`
- All commands receive context via `@click.pass_context`
- Pattern for accessing context:
```python
@click.pass_context
def my_command(ctx):
    yaml_handler = ctx.obj['yaml_handler']
    config = ctx.obj['config']
    yaml_path = ctx.obj['yaml_path']
```

**cli/integrations/tracking.py** (`TrackingIntegration` class):
- CSV-based tracking at `tracking/resume_experiment.csv`
- Methods: `log_application()`, `get_statistics()`, `update_status()`
- Status values: applied, interview, offer, rejected, withdrawn

### Variant System

Variants are defined in `resume.yaml` under `variants:`. Each variant has:
- `description`: Human-readable description
- `summary_key`: Which professional_summary to use (base or variant name)
- `skill_sections`: Which skill sections to include
- `max_bullets_per_job`: Bullet limit per experience entry
- `emphasize_keywords`: Keywords to match in bullet text

**Bullet emphasis logic**: In `get_experience(variant)` (cli/utils/yaml_parser.py), bullets are filtered by:
1. `bullet.emphasize_for` list contains variant name (e.g., "backend", "ml_ai")
2. OR `bullet.text` matches any keyword in variant's `emphasize_keywords` list
3. Fallback to first `max_bullets_per_job` bullets if none match

**Important**: When adding new experience bullets, use the `emphasize_for` field to specify which variants should include that bullet. This is the primary mechanism for variant-specific content.

### Template System

Jinja2 templates in `templates/` directory:
- `resume_md.j2`: Markdown output
- `resume_tex.j2`: LaTeX output (for PDF compilation)
- `email_md.j2`: Simple email/cover letter template
- `cover_letter_md.j2`: Full cover letter template (Markdown)
- `cover_letter_tex.j2`: Full cover letter template (LaTeX/PDF)

**Template context** includes:
- `contact`: Dict from `get_contact()`
- `summary`: String from `get_summary(variant)`
- `skills`: Dict from `get_skills(variant)`
- `experience`: List from `get_experience(variant)`
- `education`, `publications`, `certifications`, `affiliations`, `projects`

**Custom Jinja2 Filters** (defined in cli/generators/template.py):
- `latex_escape`: Escapes special LaTeX characters (&, %, $, #, _, etc.)
- `proper_title`: Title case with lowercase for small words (a, an, the, and, or, etc.)

**Important**: Jinja2 `replace()` filter takes exactly 2 args: `replace('old','new')` (no spaces around comma).

**Template Syntax Notes**:
- Use `{{ variable|latex_escape }}` for LaTeX templates to escape special characters
- Use `{% if %}` conditionals for optional content
- Access nested data with dot notation: `{{ contact.email }}`

### Configuration

`config/default.yaml` contains:
- AI provider/model settings
- Output directory and naming scheme
- Tracking CSV path
- GitHub username for sync
- Custom API base URLs for AI providers
- **Cover letter settings** (enabled, formats, smart_guesses, tone, max_length)
- **AI Judge settings** (judge_enabled, num_generations)

`Config` class (`cli/utils/config.py`) loads this with deep merge of defaults.

**Environment Variables**: The system supports `.env` files via `python-dotenv` for API keys:
- `ANTHROPIC_API_KEY`: For Claude API access
- `ANTHROPIC_BASE_URL`: Optional custom API base URL for Anthropic
- `OPENAI_API_KEY`: For OpenAI GPT API access
- `OPENAI_BASE_URL`: Optional custom API base URL for OpenAI

Copy `.env.template` to `.env` and configure your keys.

### Schema Validation

`cli/utils/schema.py` (`ResumeValidator` class):
- Validates `resume.yaml` structure
- Checks required fields, types, date formats, email format
- Validates variant skill_sections exist in skills
- Returns `ValidationError` objects with path/message/level

### GitHub Integration

`cli/integrations/github_sync.py` (`GitHubSync` class):
- Fetches repositories via GitHub CLI (`gh` command)
- Categorizes projects by keywords (AI/ML, fullstack, backend, devops, energy, tools)
- Filters by date range using `--months` parameter
- Outputs structured data for inclusion in resume.yaml
- **Project Selection**: `select_matching_projects()` method uses AI to match job technologies with repository topics/languages/descriptions, returning scored matches for auto-inclusion in resumes
- **Resume Update**: `update_resume_projects()` method inserts selected projects into the `projects.featured` section of resume.yaml

### AI-Enhanced GitHub Projects (Ephemeral Enhancement)

When using `--include-github-projects` with `generate-package`, the system now applies AI enhancements to make GitHub projects more compelling and job-relevant:

**Design Principle: Ephemeral Enhancement, Persistent Base**
- AI enhancements exist only in-memory during generation
- Base `resume.yaml` remains unchanged (no permanent modifications)
- Each job application gets customized project highlighting
- Reversible and safe - no git cleanup needed

**Enhancement Features:**

1. **Enhanced Project Descriptions** (`AIGenerator.enhance_project_descriptions()`)
   - Generates 2-3 sentence descriptions emphasizing job-relevant technologies
   - Extracts 3-5 highlighted technologies matching job requirements
   - Creates 2-4 achievement highlights (action-oriented bullets)
   - Assigns relevance score (0-10) for project ranking

2. **Professional Summary Integration** (`AIGenerator.generate_project_summary()`)
   - Seamlessly integrates 2-3 most relevant projects into summary
   - Maintains original tone and structure
   - Keeps first sentence unchanged (preserves voice)
   - Length controlled to ±20% of original

3. **Skills Prioritization** (`ResumeYAML._prioritize_skills()`)
   - Moves matching technologies to front of skill lists
   - Applied across all skill categories
   - Helps recruiters see relevant skills first

**Enhanced Project Data Structure:**
```python
{
    # Base fields from GitHub
    "name": "project-name",
    "description": "Basic description",
    "url": "https://github.com/user/project",
    "language": "Python",

    # AI-generated fields (ephemeral)
    "enhanced_description": "Built scalable Python microservice...",
    "highlighted_technologies": ["Python", "FastAPI", "Kubernetes"],
    "achievement_highlights": [
        "Reduced API latency by 40% through async optimization",
        "Implemented automated testing achieving 95% coverage"
    ],
    "relevance_score": 8.5
}
```

**Configuration Options** (`config/default.yaml`):
```yaml
github:
  enhance_descriptions: true    # Use AI to enhance project descriptions
  enhance_summary: true         # Integrate projects into professional summary
  emphasize_skills: true        # Prioritize project technologies in skills section
  emphasize_experience: false   # Future: emphasize relevant experience bullets
```

**Usage:**
```bash
resume-cli generate-package \
  --job-desc job-posting.txt \
  --include-github-projects \
  --variant v1.1.0-backend
```

**Output Differences:**
- Projects section includes enhanced descriptions, technology lists, achievement highlights
- Professional summary mentions relevant projects
- Skills section prioritizes project technologies
- All enhancements are ephemeral (resume.yaml unchanged)

**Error Handling:**
- Graceful degradation if AI fails (uses original descriptions)
- User warnings for partial failures
- Configurable feature flags (can disable specific enhancements)

**Important:**
- Enhancements do NOT modify `resume.yaml` permanently
- Each job application gets fresh, tailored enhancements
- Truthfulness enforced: AI prompts emphasize "do NOT invent features"
- Achievements extracted from project metadata, not hallucinated

### Initialization Command

`cli/commands/init.py` (`init_command`):
- Parses existing resume files from `resumes/` directory
- Creates structured `resume.yaml` from flat text resumes
- Interactive prompts for missing information

## Working with Resume Data

### Adding a New Job/Experience

Edit `resume.yaml`:

```yaml
experience:
  - company: "Company Name"
    title: "Job Title"
    start_date: "2024-01"  # YYYY-MM format
    end_date: null  # null for current position
    location: "City, ST"
    bullets:
      - text: "What you accomplished..."
        skills: ["Python", "Kubernetes"]
        emphasize_for: ["backend", "devops"]  # Variants to emphasize
```

### Adding a New Variant

1. Add summary to `professional_summary.variants:` in `resume.yaml`
2. Add variant config to `variants:` in `resume.yaml`
3. Optionally add `emphasize_for` hints to relevant bullets
4. Test with `resume-cli generate -v vX.Y.Z-NAME -f md`

### Modifying Templates

Edit files in `templates/` directory:
- Templates use Jinja2 syntax
- Context variables passed from `TemplateGenerator.generate()`
- Test changes with `resume-cli generate --no-save` to preview

### Adding AI Customization

1. Install AI dependencies: `pip install -e ".[ai]"`
2. Set API key environment variable or add to `.env` file
3. Run: `resume-cli generate --ai --job-desc job-posting.txt`

AI generator will:
- Extract keywords from job description
- Reorder bullets to emphasize relevant experience
- Highlight matching skills
- Keep all content truthful (no fake experience)
- Optionally use AI Judge to select best of N generations (configurable)

**AI Configuration**:
- Provider and model are set in `config/default.yaml` under `ai:` section
- Default: `provider: anthropic`, `model: claude-3-5-sonnet-20241022`
- AI Judge: Enable with `ai.judge_enabled: true` and set `ai.num_generations: 3`
- Custom API base URLs supported (e.g., for OpenRouter, z.ai, or other proxies)

### Generating Application Packages (Resume + Cover Letter)

The `generate-package` command creates a complete application package:

```bash
# Interactive mode (AI asks questions for cover letter)
resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend

# Non-interactive mode (uses smart guesses)
resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive

# Generate PDF resume and cover letter
resume-cli generate-package --job-desc job.txt -f pdf --variant v1.2.0-ml_ai
```

**Output Structure:**
```
output/
└── {company}-{date}/
    ├── resume.md         # AI-customized resume (Markdown)
    ├── resume.pdf        # AI-customized resume (PDF)
    ├── cover-letter.md   # Cover letter (Markdown)
    └── cover-letter.pdf  # Cover letter (PDF)
```

**Note**: The `generate-package` command always produces both MD and PDF formats for both resume and cover letter. The `-f/--format` option is deprecated and ignored.

**Important**: When using `--include-github-projects`:
- **Previous behavior**: Modified `resume.yaml` permanently with selected projects
- **New behavior**: Applies AI enhancements **ephemerally** (in-memory only)
  - Enhanced project descriptions, technology highlights, achievement bullets
  - Professional summary integrates relevant projects
  - Skills section prioritizes project technologies
  - **resume.yaml remains unchanged** - no git cleanup needed!
- Recommended: Commit changes before running for peace of mind, but no longer required

**Interactive Mode Questions:**
1. What excites you about this role? (required)
2. What aspects of the company's mission resonate with you? (optional)
3. Do you have any connections at the company? (optional)

**Non-Interactive Mode:**
- AI generates smart guesses for cover letter content
- Analyzes job requirements vs. resume experience
- Creates appropriate motivation and alignment statements
- Skips optional sections (connections) unless clear from context

**Auto-Selecting GitHub Projects** (`--include-github-projects` flag):
- Extracts top technologies from job description using AI
- Searches GitHub repos (including organization code) for matching projects
- Selects up to `github.max_projects` best matches based on topic/language/description relevance
- **NEW**: Applies AI enhancements to selected projects (ephemeral - in-memory only)
  - Enhanced descriptions emphasizing job-relevant technologies
  - Highlighted technologies and achievement highlights
  - Integrated into professional summary and prioritized in skills section
- Useful for showcasing relevant work for each application

## File Structure Notes

- `resume.yaml`: Edit this to update resume content
- `cli/`: Package containing all CLI code
  - `cli/main.py`: Click CLI entry point with `@click.group()` decorator
  - `cli/commands/`: Command implementations (`init.py`)
  - `cli/generators/`: Template and AI generators
  - `cli/integrations/`: External service integrations (tracking, GitHub)
  - `cli/utils/`: Core utilities (YAML parser, config, schema validation)
- `templates/`: Jinja2 templates (add new formats here)
- `config/`: Configuration files
- `output/`: Generated resumes (auto-created, dates in filenames)
- `tracking/`: Application tracking CSV (auto-created)

**Package Entry Point**: The `resume-cli` command is registered in `setup.py` as:
```python
entry_points={
    "console_scripts": [
        "resume-cli=cli.main:main",
    ],
}
```

This allows invocation via `resume-cli` after installation.

## PDF Generation

Requires LaTeX tools:

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full
```

**Fedora/RPM-based (Fedora, RHEL, CentOS):**
```bash
sudo dnf install texlive-scheme-full
```

**macOS:**
```bash
brew install mactex
```

**Or use Pandoc (smaller footprint):**
```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-xetex

# Fedora/RPM-based
sudo dnf install pandoc texlive-xetex
```

PDF compilation happens in `TemplateGenerator._compile_pdf()` (cli/generators/template.py) via:
1. First attempts: `pdflatex` (full LaTeX distribution)
2. Fallback: `pandoc` (if pdflatex unavailable)

**Note**: PDF generation is significantly slower than Markdown/TEX due to compilation.

## ATS (Applicant Tracking System) Checking

The `ats-check` command analyzes resume compatibility with automated screening systems.

### Usage

```bash
# Check ATS score for a specific variant
resume-cli ats-check -v v1.1.0-backend --job-desc job-posting.txt

# Save report as JSON
resume-cli ats-check --job-desc job.txt --output ats-report.json
```

### Scoring System

The ATS checker evaluates 5 categories (100 points total):

**1. Format Parsing (20pts)**
- Checks if resume is in text-extractable format
- Validates no images/tables that block ATS parsers
- Checks for minimal special characters

**2. Keywords (30pts)**
- Uses AI to extract key requirements from job description
- Compares against resume skills and experience
- Falls back to regex-based extraction if AI unavailable
- Returns missing keywords for improvement

**3. Section Structure (20pts)**
- Validates presence of standard ATS sections:
  - Experience (preferred first)
  - Education
  - Skills
  - Professional summary

**4. Contact Info (15pts)**
- Checks email format validity
- Verifies phone and location presence
- Bonus for LinkedIn/GitHub links

**5. Readability (15pts)**
- Detects action verbs in experience bullets
- Checks for quantifiable metrics (e.g., "increased by 30%")
- Validates use of bullet points
- Checks for excessive acronyms

### Sample Output

```
ATS Score: 81/100 (81%)

Good! Your resume is ATS-friendly with room for improvement.

Category Breakdown:
✓ Format Parsing: 20/20 (100%)
  Structured text format (no images)
  No tables detected (ATS-friendly)
  Minimal special characters (good)

✗ Keywords: 14/30 (47%)
  Job keywords found: 15
  Matching keywords: 7
  Top matches: kubernetes, postgresql, fastapi, python, docker
  Missing keywords: microservices, communication, graphql, agile, ci/cd
  Suggestions:
    • Add these keywords to skills or experience: microservices, communication...

✓ Section Structure: 20/20 (100%)
  ✓ Experience section present
  ✓ Education section present
  ✓ Skills section present
  ✓ Summary section present

✓ Contact Info: 15/15 (100%)
  ✓ Email present and valid
  ✓ Phone present and valid
  ✓ Location present

✗ Readability: 12/15 (80%)
  ✓ Uses action verbs (3 found)
  ✓ Minimal acronyms (0 found)
  ✓ Uses bullet points for experience
  Suggestions:
    • Add quantifiable metrics (e.g., 'increased by 30%')

Top Recommendations:
  1. Add these keywords to skills or experience: microservices, communication...
  2. Add quantifiable metrics (e.g., 'increased by 30%')
```

### Implementation Details

`cli/generators/ats_generator.py` (`ATSGenerator` class):
- `generate_report()`: Main method to generate complete ATS report
- `_check_format_parsing()`: Validates text format
- `_check_keywords()`: AI-powered keyword extraction and matching
- `_check_section_structure()`: Validates ATS-required sections
- `_check_contact_info()`: Validates contact information
- `_check_readability()`: Checks action verbs, metrics, formatting
- `print_report()`: Formats and displays report using Rich console
- `export_json()`: Saves report as JSON for programmatic access

**AI Integration**: The ATS checker uses AI for intelligent keyword extraction when available (Anthropic/OpenAI). Falls back to regex-based extraction if AI is unavailable or API keys are not configured.

**Configuration**: ATS settings in `config/default.yaml`:
```yaml
ats:
  enabled: true
  scoring:
    format_parsing: 20
    keywords: 30
    section_structure: 20
    contact_info: 15
    readability: 15
```

## ResumeAI Integration

resume-cli and ResumeAI use different data schemas:
- **resume-cli**: Uses YAML format with variants support
- **ResumeAI**: Uses JSON Resume format (https://jsonresume.org/schema/)

### Converting Between Formats

The CLI provides conversion commands:

```bash
# Export resume-cli YAML to JSON Resume (for ResumeAI)
resume-cli convert resume.yaml resume.json --to-json

# Or use the convenience command
resume-cli export-json-resume resume.yaml -o resume.json

# Import JSON Resume to resume-cli YAML
resume-cli convert resume.json resume.yaml --to-yaml

# Or use the convenience command
resume-cli import-json-resume resume.json -o resume.yaml
```

### JSON Resume Converter

The `cli/utils/json_resume_converter.py` module provides bidirectional conversion:
- `JSONResumeConverter.yaml_to_json_resume()`: Convert YAML to JSON Resume format
- `JSONResumeConverter.json_resume_to_yaml()`: Convert JSON Resume to YAML format

### Schema Compatibility

The schema validator (`cli/utils/schema.py`) supports both formats:
- Fields like `studyType`, `endDate`, `area` are accepted (JSON Resume format)
- Projects can be either dict or list format

This ensures compatibility between the two systems.

## Error Handling and Troubleshooting

### Common Issues

**"resume.yaml not found"**
- Run `resume-cli init --from-existing` to create from existing files
- Or ensure you're in the correct directory

**"anthropic package not installed"**
- Install AI dependencies: `pip install -e ".[ai]"`
- The base install doesn't include AI packages

**"ANTHROPIC_API_KEY not set"**
- Set environment variable: `export ANTHROPIC_API_KEY=your_key`
- Or create `.env` file from `.env.template`

**"PDF compilation failed"**
- Install LaTeX tools (see PDF Generation section above)
- Check that `pdflatex` or `pandoc` is in your PATH

**"gh command not found"**
- Install GitHub CLI: https://cli.github.com/
- Required for `resume-cli sync-github` command

**"ModuleNotFoundError: No module named 'cli'"**
- Ensure you installed with `pip install -e .` in the project root
- The editable install is required for the `resume-cli` command to work

### Validation Errors

Run `resume-cli validate` to check for:
- Missing required fields in resume.yaml
- Invalid date formats (use YYYY-MM format)
- Invalid email addresses
- Mismatched skill sections in variants

### AI Generation Issues

**API errors**: Check your API key and network connection
**Rate limiting**: The system will automatically retry with exponential backoff
**Fallback**: If AI generation fails completely, it falls back to template-based generation (configurable via `ai.fallback_to_template`)
**Custom API providers**: Set `ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` in `.env` to use alternative API endpoints (e.g., OpenRouter, z.ai)

**Project enhancement failures**:
- If `enhance_project_descriptions()` fails, uses original GitHub descriptions
- If `generate_project_summary()` fails, uses base professional summary
- Check console warnings for specific error messages
- Disable specific enhancements in `config/default.yaml`:
  ```yaml
  github:
    enhance_descriptions: false
    enhance_summary: false
    emphasize_skills: false
  ```

## Development Workflow

1. Edit `resume.yaml` to add/update content
2. Run `resume-cli validate` to check for errors
3. Run `resume-cli generate -v v1.0.0-base --no-save` to preview changes
4. When satisfied, generate specific variant: `resume-cli generate -v v1.1.0-backend -f md`
5. For job applications: `resume-cli generate-package --job-desc job.txt --variant v1.1.0-backend`
6. Track applications: `resume-cli apply Company applied -r "Job Title"`

## Key Concepts

### Emphasis System for Variants

The emphasis system controls which bullets appear in which variants. Bullets are filtered by two mechanisms in `get_experience(variant)`:

1. **Direct variant targeting**: Set `emphasize_for: ["backend", "devops"]` on a bullet to include it in specific variants
2. **Keyword matching**: Variant configs define `emphasize_keywords` list; bullets matching these keywords are included

**Best practice**: Use `emphasize_for` for explicit targeting. Keyword matching is a fallback for when you don't control the bullet content.

### AI Judge Pattern

The AI Judge (`cli/generators/ai_judge.py`) implements quality control:
1. Generate N versions of content (resume or cover letter)
2. Judge evaluates each version against job requirements
3. Returns best version OR combines elements from multiple versions
4. Configurable via `ai.judge_enabled` and `ai.num_generations`

This pattern improves output quality by reducing randomness in AI generation.

### Resume API Server

The system includes a FastAPI-based REST API server for programmatic resume generation:

**api/main.py** - FastAPI application with endpoints:
- `GET /v1/variants` - List available resume variants (API key required)
- `POST /v1/render/pdf` - Render resume as PDF from YAML data (API key required)
- `POST /v1/tailor` - AI-tailor resume data for job description (API key required)

**api/models.py** - Pydantic models for API requests:
- `ResumeRequest` - Contains `resume_data` dict and `variant` string
- `TailorRequest` - Contains `resume_data` dict and `job_description` string

**api/auth.py** - API key authentication via `get_api_key()` dependency

**API Security:**
- All endpoints require API key via `Security(get_api_key)` dependency
- API key is checked from `API_KEY` environment variable
- Returns 401 if API key is missing or invalid

**Usage:**
```bash
# Start API server
python -m api.main

# Or via uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**API Dependencies:**
- `fastapi` - Web framework
- `pydantic` - Request/response validation
- `uvicorn` - ASGI server (for running)
- Reuses `TemplateGenerator` and `AIGenerator` from CLI

**Note**: The API server creates temporary YAML files for rendering and returns PDF bytes directly in the response.
