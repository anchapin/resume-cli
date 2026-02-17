# Resume CLI System

[![CI](https://github.com/anchapin/job-hunt/actions/workflows/ci.yml/badge.svg)](https://github.com/anchapin/job-hunt/actions/workflows/ci.yml)
[![Lint](https://github.com/anchapin/job-hunt/actions/workflows/lint.yml/badge.svg)](https://github.com/anchapin/job-hunt/actions/workflows/lint.yml)
[![Security](https://github.com/anchapin/job-hunt/actions/workflows/security.yml/badge.svg)](https://github.com/anchapin/job-hunt/actions/workflows/security.yml)

A unified command-line interface for generating job-specific resumes from a single YAML source. Supports fast template-based generation and AI-powered customization with full integration into application tracking.

## Features

- **Single Source of Truth**: Store all resume data in `resume.yaml`
- **Fast Generation**: Create any variant in <1 second using Jinja2 templates
- **AI-Powered**: Optional AI customization using Claude or OpenAI
- **ATS Compatibility**: Check resume optimization for automated screening systems
- **Multiple Variants**: 6 pre-configured variants (base, backend, ML/AI, fullstack, DevOps, leadership)
- **Multiple Formats**: Output to Markdown, LaTeX, or PDF
- **Application Tracking**: Built-in CSV tracking with analytics
- **GitHub Integration**: Sync projects automatically
- **LinkedIn Integration**: Import/export LinkedIn profile data
- **Schema Validation**: Catch errors before generating

## Installation

### Prerequisites

- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12 (tested in CI)
- **LaTeX** (optional, for PDF generation): See PDF Generation section

### From Source

```bash
cd /path/to/job_hunt
pip install -e .
```

### With AI Support

```bash
pip install -e ".[ai]"
```

This installs the required AI API packages:
- `anthropic` for Claude
- `openai` for GPT models
- `python-dotenv` for environment variable management

## Quick Start

### 1. Set up your resume data

**Option A: Start from scratch (recommended)**

Copy the example resume file and customize it:

```bash
cp resume.example.yaml resume.yaml
# Edit resume.yaml with your information
```

**Option B: Import from existing resume**

If you have existing resume files:

```bash
resume-cli init --from-existing
```

This parses `resumes/base_resume.txt` and creates `resume.yaml`.

### 2. Generate a resume

```bash
# Generate base variant as Markdown
resume-cli generate -v v1.0.0-base -f md

# Generate backend variant as PDF
resume-cli generate -v v1.1.0-backend -f pdf

# List all available variants
resume-cli variants
```

### 3. Validate your data

```bash
resume-cli validate
```

## Commands

### generate

Generate a resume from template or AI.

```bash
resume-cli generate [OPTIONS]

Options:
  -v, --variant TEXT      Resume variant (default: v1.0.0-base)
  -f, --format CHOICE     Output format: md, tex, pdf (default: md)
  -o, --output PATH       Output file path
  --no-save              Print to stdout without saving
  --ai                   Use AI-powered generation (requires --job-desc)
  --job-desc PATH        Path to job description file (required for --ai)
```

**Examples:**

```bash
# Generate Markdown resume (template-based)
resume-cli generate -v v1.0.0-base -f md

# Generate PDF with custom output path
resume-cli generate -v v1.1.0-backend -f pdf -o my-resume.pdf

# AI-customized for specific job
resume-cli generate --ai --job-desc job-posting.txt

# Preview without saving
resume-cli generate -v v1.2.0-ml_ai --no-save
```

**Note:** The `--ai` flag requires `--job-desc`. Without `--ai`, generation uses fast templates (<1 second).

### variants

List all available resume variants.

```bash
resume-cli variants
```

### ats-check

Check ATS (Applicant Tracking System) compatibility score.

Analyzes resume against job description and provides actionable feedback for optimization.

```bash
resume-cli ats-check [OPTIONS]

Options:
  --job-desc PATH        Path to job description file (required)
  -v, --variant TEXT     Resume variant to check (default: v1.0.0-base)
  --output PATH          Save report as JSON file
```

**Scoring Categories:**

- **Format Parsing** (20pts): Text extraction and formatting checks
- **Keywords** (30pts): Job keyword matching (uses AI if available, falls back to regex)
- **Section Structure** (20pts): Standard ATS sections validation
- **Contact Info** (15pts): Email, phone, location verification
- **Readability** (15pts): Action verbs, metrics, bullet points

**Examples:**

```bash
# Check ATS score for backend variant
resume-cli ats-check -v v1.1.0-backend --job-desc job-posting.txt

# Save report as JSON
resume-cli ats-check --job-desc job.txt --output ats-report.json
```

**Sample Output:**

```
ATS Score: 81/100 (81%)

Good! Your resume is ATS-friendly with room for improvement.

Category Breakdown:
✓ Format Parsing: 20/20
✗ Keywords: 14/30 - Missing: Kubernetes, CI/CD
✓ Section Structure: 20/20
✓ Contact Info: 15/15
✗ Readability: 12/15

Top Recommendations:
  1. Add these keywords to skills or experience: Kubernetes, CI/CD
  2. Add quantifiable metrics (e.g., 'increased by 30%')
```

### validate

Validate `resume.yaml` schema and data.

```bash
resume-cli validate
```

### generate-package

Generate a complete application package: AI-customized resume + cover letter.

**Note:** This command **automatically uses AI customization** when a job description is provided. No `--ai` flag is needed or available.

```bash
resume-cli generate-package [OPTIONS]

Options:
  --job-desc PATH        Path to job description file (required)
  -v, --variant TEXT     Resume variant (default: v1.0.0-base)
  --company TEXT         Company name (overrides extraction from job description)
  --non-interactive      Skip questions, use smart defaults
  --no-cover-letter      Skip cover letter generation
  --output-dir PATH      Output directory (default: config setting)
  --include-github-projects  Auto-select GitHub projects matching job technologies
```

**Output Structure:**

```
output/{company}-{date}/
├── resume.md
├── resume.pdf
├── cover-letter.md
└── cover-letter.pdf
```

**Examples:**

```bash
# Interactive mode (asks questions for cover letter)
resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend

# Non-interactive mode (uses smart guesses)
resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive

# With GitHub projects auto-selected based on job technologies (AI is automatic)
resume-cli generate-package --job-desc job-posting.txt --variant v1.2.0-ml_ai --include-github-projects

# Note: No --ai flag needed - AI customization is automatic with --job-desc
```

### apply

Log a job application to tracking CSV.

```bash
resume-cli apply COMPANY STATUS [OPTIONS]

Arguments:
  COMPANY     Company name
  STATUS      Application status

Options:
  -r, --role TEXT       Job role/title
  -v, --variant TEXT    Resume variant used
  -s, --source TEXT     Application source
  -u, --url TEXT        Job posting URL
  -n, --notes TEXT      Additional notes
```

**Examples:**

```bash
# Log new application
resume-cli apply Google applied -r "Senior Backend Engineer"

# Update status
resume-cli apply Google interview -v v1.1.0-backend

# With details
resume-cli apply Stripe offer -r "Staff Engineer" -s "Referral" -u "https://stripe.com/jobs"
```

**Valid statuses:**
- `applied` - Application submitted
- `interview` - Interview scheduled
- `offer` - Offer received
- `rejected` - Application rejected
- `withdrawn` - Withdrew application

### analyze

Show application tracking analytics.

```bash
resume-cli analyze
```

### sync-github

Sync GitHub projects to resume.yaml.

```bash
resume-cli sync-github [OPTIONS]

Options:
  --months INTEGER  Number of months to look back (default: 3)
```

**Requirements:**
- GitHub CLI (`gh`) installed and authenticated
- Run `gh auth login` first if needed

### linkedin-import

Import LinkedIn profile data into resume.yaml.

```bash
resume-cli linkedin-import [OPTIONS]

Options:
  --data-file PATH     Path to LinkedIn exported JSON or CSV data file (required)
  --output PATH        Output YAML file path (default: resume.yaml)
  --merge              Merge with existing resume.yaml instead of overwriting
  --dry-run            Preview changes without writing to file
```

**Important:** Direct URL import is not supported due to LinkedIn API restrictions. You must export your LinkedIn data first.

**To get all your data (experience, education, skills, certifications):**

1. Go to https://www.linkedin.com/psettings/member-data
2. Click "Request data archive" (NOT just "Profile" data)
3. Wait for LinkedIn to prepare your download (may take a few minutes to hours)
4. Download the ZIP file containing your data
5. Extract the ZIP file - look for JSON files (e.g., `profile.json`, `experience.json`, `education.json`, `skills.json`)
6. Use the main profile JSON file with `--data-file`

**Note:** The basic "Profile" export (Profile.csv) only contains basic fields (name, headline, summary). It does NOT include experience, education, skills, or certifications. You must request the full data archive to get those.

**Examples:**

```bash
# Import from exported JSON (creates new resume.yaml)
resume-cli linkedin-import --data-file profile.json

# Merge with existing resume.yaml
resume-cli linkedin-import --data-file profile.json --merge

# Preview changes before importing
resume-cli linkedin-import --data-file profile.json --dry-run

# Import to custom path
resume-cli linkedin-import --data-file profile.json --output my-resume.yaml
```

**Field Mapping:**

| LinkedIn Field | resume.yaml Field |
|----------------|------------------|
| firstName/lastName | contact.name |
| email | contact.email |
| phone | contact.phone |
| location | contact.location |
| headline/summary | professional_summary.base |
| skills | skills.* (auto-categorized) |
| experience | experience |
| education | education |
| certifications | certifications |

### linkedin-export

Export resume.yaml data to LinkedIn-friendly format.

```bash
resume-cli linkedin-export [OPTIONS]

Options:
  -v, --variant TEXT    Resume variant to export (default: v1.0.0-base)
  -o, --output PATH    Output file path (default: output/linkedin-update.txt)
  --format CHOICE      Output format: linkedin, plain (default: linkedin)
```

**Examples:**

```bash
# Export for LinkedIn update
resume-cli linkedin-export

# Export specific variant
resume-cli linkedin-export -v v1.1.0-backend

# Export to custom file
resume-cli linkedin-export -o my-linkedin-update.txt

# Export plain text format
resume-cli linkedin-export --format plain
```

**Note:** LinkedIn has character limits for each field. You may need to trim bullets to fit LinkedIn's format.

### init

Initialize resume.yaml from existing resume files.

```bash
resume-cli init [OPTIONS]

Options:
  --from-existing    Parse existing resume files
```

## resume.yaml Structure

The single source of truth for all resume data:

```yaml
meta:
  version: "2.0.0"
  last_updated: "2025-02-03"

contact:
  name: "Your Name"
  credentials: ["P.E."]
  phone: "555-123-4567"
  email: "you@example.com"
  location:
    city: "City"
    state: "ST"
    zip: "12345"
  urls:
    github: "https://github.com/username"
    linkedin: "https://linkedin.com/in/username"

professional_summary:
  base: "Default summary for all variants..."
  variants:
    backend: "Specialized backend summary..."
    ml_ai: "ML/AI focused summary..."

skills:
  programming_languages:
    - { name: "Python", level: "Expert", years: 8 }
  cloud_devops:
    - { name: "AWS", services: ["EKS", "EC2"] }

experience:
  - company: "Company Name"
    title: "Job Title"
    start_date: "2022-04"
    end_date: null  # null = current
    bullets:
      - text: "Achievement description..."
        skills: ["DevOps", "Kubernetes"]
        emphasize_for: ["backend", "devops"]

variants:
  v1.0.0-base:
    description: "General software engineering"
    summary_key: "base"
    skill_sections: ["programming_languages", "cloud_devops"]
    max_bullets_per_job: 4
```

## Variants

### v1.0.0-base
General software engineering with balanced focus on all skills.

### v1.1.0-backend
Backend & DevOps specialization. Emphasizes backend technologies, cloud infrastructure, databases, and APIs.

### v1.2.0-ml_ai
ML/AI specialization. Emphasizes AI/ML frameworks, data engineering, model deployment, and Python/PyTorch.

### v1.3.0-fullstack
Full-stack specialization. Emphasizes frontend and backend balance and modern web frameworks.

### v1.4.0-devops
DevOps & Infrastructure specialization. Emphasizes Kubernetes, Docker, CI/CD, and cloud platforms.

### v1.5.0-leadership
Leadership & Technical Staff. Emphasizes architecture, mentoring, and technical strategy.

## AI-Powered Generation

### Setup

1. Install AI dependencies:
   ```bash
   pip install -e ".[ai]"
   ```

2. Create `.env` file with API keys:
   ```bash
   cp .env.template .env
   # Edit .env to add your keys
   ```

3. Configure API keys in `.env`:

   **For Claude (Anthropic):**
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

   **For OpenAI:**
   ```
   OPENAI_API_KEY=your_key_here
   ```

   **Optional: Custom API endpoints** (e.g., for z.ai, OpenRouter, or other proxies):
   ```
   ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
   OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
   ```

4. Configure provider in `config/default.yaml`:
   ```yaml
   ai:
     provider: anthropic  # or openai
     model: claude-3-5-sonnet-20241022
   ```

### Usage

**For resume generation with AI:**
```bash
# Use --ai flag with generate command
resume-cli generate --ai --job-desc job-posting.txt

# AI will:
# 1. Extract key requirements from job description
# 2. Reorder bullets to emphasize relevant experience
# 3. Highlight matching skills
# 4. Keep all content truthful (no fake experience)
```

**For complete application packages (resume + cover letter):**
```bash
# generate-package automatically uses AI - no --ai flag needed!
resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend

# This generates both AI-customized resume AND cover letter
```

### Troubleshooting AI Errors

**"anthropic package not installed"**
```bash
# Install AI dependencies
pip install -e ".[ai]"
```

**"ANTHROPIC_API_KEY not set"**
- Make sure you created a `.env` file from `.env.template`
- Verify the API key is set correctly in `.env`
- `python-dotenv` loads environment variables from `.env` automatically

**"OPENAI_API_KEY not set"**
- Same troubleshooting steps as ANTHROPIC_API_KEY above

**API connection errors**
- Check your network connection
- Verify API key is valid
- If using custom `BASE_URL`, verify the endpoint is correct

**"AI generation failed, falling back to template"**
- This is expected behavior when AI API fails
- The system automatically falls back to fast template generation
- Check API key validity and network connection to use AI features
- Set `ai.fallback_to_template: false` in config to fail instead of falling back

**"No such option: --ai" with generate-package**
- The `generate-package` command **does not have an `--ai` flag**
- AI customization is automatic when you provide `--job-desc`
- Simply run: `resume-cli generate-package --job-desc job-posting.txt`
- Use `resume-cli generate --ai --job-desc ...` if you only want an AI-customized resume without cover letter

## Configuration

Edit `config/default.yaml` to customize:

```yaml
output:
  directory: output
  naming_scheme: "resume-{variant}-{date}.{ext}"
  date_format: "%Y-%m-%d"

generation:
  default_variant: v1.0.0-base
  default_format: md
  max_bullets: 4

ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  fallback_to_template: true
  # Multi-generation with AI Judge
  judge_enabled: true  # Use AI judge to select best of N generations
  num_generations: 3   # Number of versions to generate for judge evaluation
  # Optional: Custom API base URLs (can also be set in .env)
  anthropic_base_url: ""
  openai_base_url: ""

tracking:
  enabled: true
  csv_path: tracking/resume_experiment.csv

cover_letter:
  enabled: true
  formats: [md, pdf]
  smart_guesses: true
  tone: professional
  max_length: 400

github:
  username: your_username
  sync_months: 3
  # Auto-projects feature for generate-package
  max_projects: 3

linkedin:
  # LinkedIn import/export settings
  import_merge_mode: merge      # Options: merge, overwrite
  export_format: linkedin       # Options: linkedin, plain
  output_directory: output     # Default directory for LinkedIn exports
```

## PDF Generation

PDF generation requires LaTeX tools:

### Ubuntu/Debian
```bash
sudo apt-get install texlive-full
```

### Fedora/RPM-based (Fedora, RHEL, CentOS)
```bash
sudo dnf install texlive-scheme-full
```

### macOS
```bash
brew install mactex
```

### Or use Pandoc
```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-xetex

# Fedora/RPM-based
sudo dnf install pandoc texlive-xetex
```

## File Structure

```
job_hunt/
├── resume.yaml              # Single source resume data
├── cli/                     # CLI package
│   ├── main.py              # Entry point
│   ├── commands/            # Command implementations
│   ├── generators/          # Template + AI engines
│   ├── integrations/        # Tracking, GitHub, LinkedIn, etc.
│   └── utils/               # YAML parser, schema, config
├── templates/               # Jinja2 templates
│   ├── resume_md.j2
│   ├── resume_tex.j2
│   └── cover_letter_md.j2
├── config/                  # Configuration files
│   ├── default.yaml
│   └── variants.yaml
├── output/                  # Generated resumes
├── tracking/                # Application tracking CSV
├── requirements.txt         # Python dependencies
└── setup.py                 # Package installation
```

## Troubleshooting

### "resume.yaml not found"
- Run `resume-cli init --from-existing` to create from existing files
- Or copy `resume.example.yaml` to `resume.yaml` and customize

### "anthropic package not installed"
```bash
pip install -e ".[ai]"
```

### "ANTHROPIC_API_KEY not set"
- Create `.env` file from `.env.template`
- Add your API key to `.env`
- The system automatically loads variables from `.env`

### "PDF compilation failed"
- Install LaTeX tools (see PDF Generation section above)
- Ensure `pdflatex` or `pandoc` is in your PATH

### "gh command not found"
- Install GitHub CLI: https://cli.github.com/
- Required for `resume-cli sync-github` command

## Development

### Running Tests

```bash
pytest
```

### Adding New Variants

1. Add variant to `resume.yaml` under `variants:`
2. Optionally add variant-specific summary to `professional_summary.variants:`
3. Run `resume-cli generate -v v1.X.Y-variant`

### Adding New Template Formats

1. Create Jinja2 template in `templates/`
2. Add format choice to `generate` command in `cli/main.py`
3. Update `TemplateGenerator` in `cli/generators/template.py`

## License

MIT License - See LICENSE file for details.

## Roadmap

### Current Version: v2.0.0

**Completed Features:**
- ✅ Core CLI with template-based generation (Jinja2)
- ✅ Multiple output formats (Markdown, LaTeX, PDF)
- ✅ AI-powered resume tailoring (Claude/OpenAI)
- ✅ Cover letter generation (interactive + non-interactive)
- ✅ Application tracking (CSV-based analytics)
- ✅ GitHub project sync and AI enhancement
- ✅ AI Judge for multi-generation quality selection
- ✅ REST API server for programmatic access
- ✅ Schema validation and configuration management
- ✅ 6 pre-configured resume variants

---

### Short-Term (1-3 Months)

**Quality & Testing**
- [ ] Comprehensive test coverage (pytest for all modules)
- [ ] Integration tests for CLI commands
- [ ] Mock testing for AI API calls
- [ ] Performance benchmarking for large resume.yaml files

**User Experience**
- [ ] Better error messages and actionable guidance
- [ ] Progress indicators for long-running operations
- [ ] Resume diff/comparison between variants
- [ ] "What changed" log when updating resume.yaml

**Template Enhancements**
- [ ] Additional resume templates (modern, minimalist, academic)
- [ ] Cover letter templates with different tones
- [ ] User-provided custom template support
- [ ] Template preview mode

**Documentation**
- [ ] Interactive tutorials for each command
- [ ] Video walkthrough for quick onboarding
- [ ] Troubleshooting guide for common issues

---

### Medium-Term (3-6 Months)

**ATS Optimization**
- [ ] ATS score checker (parse-friendly format validation)
- [ ] Keyword density analysis
- [ ] Resume format recommendations for popular ATS systems
- [ ] Export to ATS-friendly formats (plain text, docx)

**Job Board Integration**
- [ ] LinkedIn profile import/export
- [ ] Indeed/LinkedIn job posting parser
- [ ] Automated application logging (with manual approval)
- [ ] Job search aggregator integration

**Advanced Analytics**
- [ ] Visual dashboard for application metrics
- [ ] Response rate heatmaps by company size/location
- [ ] Variant performance A/B testing tools
- [ ] Export analytics to CSV/JSON for external analysis

**Multi-Device Support**
- [ ] Mobile-responsive web interface
- [ ] Desktop application (Electron/Tauri)
- [ ] Cross-platform sync via cloud storage
- [ ] Offline mode with local AI models

---

### Long-Term (6-12+ Months)

**Interview Preparation**
- [ ] AI-generated interview questions based on job description
- [ ] Mock interview mode with AI interviewer
- [ ] Company research aggregation (news, culture, recent wins)
- [ ] STAR method response templates

**Networking & Career Growth**
- [ ] Connection finder (find alumni/connections at target companies)
- [ ] Salary research and market data integration
- [ ] Offer comparison tool with negotiation suggestions
- [ ] Personal branding assistant (LinkedIn, portfolio suggestions)

**Enterprise Features**
- [ ] Team collaboration mode (shared resume reviews)
- [ ] Template marketplace for resume designs
- [ ] Recruiter dashboard for hiring teams
- [ ] API rate limiting and usage analytics

**Advanced AI Features**
- [ ] Multi-language resume generation
- [ ] Video resume generation support
- [ ] Portfolio project recommendations
- [ ] Skill gap analysis vs. job requirements

**Platform Expansion**
- [ ] Browser extension for auto-fill applications
- [ ] Mobile app for iOS/Android
- [ ] Plugin ecosystem for third-party integrations
- [ ] White-label offering for career coaches

---

### Requested Features

Help us prioritize! If you'd like to see a feature, please:
1. Check existing GitHub issues
2. Create a new issue with the `enhancement` label
3. Include use cases and why it matters to you

**Most requested (community-driven):**
- 📊 ATS optimization tools
- 🌐 Web UI
- 📱 Mobile companion app
- 🤝 Collaboration features

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
- Run `resume-cli validate` to check for errors
- Check documentation in `docs/`
- Review `tracking/` for application history
