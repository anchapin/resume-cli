# Resume CLI System

A unified command-line interface for generating job-specific resumes from a single YAML source. Supports fast template-based generation and AI-powered customization with full integration into application tracking.

## Features

- **Single Source of Truth**: Store all resume data in `resume.yaml`
- **Fast Generation**: Create any variant in <1 second using Jinja2 templates
- **AI-Powered**: Optional AI customization using Claude or OpenAI
- **Multiple Variants**: 6 pre-configured variants (base, backend, ML/AI, fullstack, DevOps, leadership)
- **Multiple Formats**: Output to Markdown, LaTeX, or PDF
- **Application Tracking**: Built-in CSV tracking with analytics
- **GitHub Integration**: Sync projects automatically
- **Schema Validation**: Catch errors before generating

## Installation

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
  --ai                   Use AI-powered generation
  --job-desc PATH        Path to job description file
```

**Examples:**

```bash
# Generate Markdown resume
resume-cli generate -v v1.0.0-base -f md

# Generate PDF with custom output path
resume-cli generate -v v1.1.0-backend -f pdf -o my-resume.pdf

# AI-customized for specific job
resume-cli generate --ai --job-desc job-posting.txt -v v1.1.0-backend

# Preview without saving
resume-cli generate -v v1.2.0-ml_ai --no-save
```

### variants

List all available resume variants.

```bash
resume-cli variants
```

Output:

```
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Variant           ┃ Description          ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ v1.0.0-base       │ General software     │
│                   │ engineering          │
│ v1.1.0-backend    │ Backend & DevOps     │
│ v1.2.0-ml_ai      │ ML/AI specialization │
│ v1.3.0-fullstack  │ Full-stack           │
│ v1.4.0-devops     │ DevOps &             │
│                   │ Infrastructure       │
│ v1.5.0-leadership │ Leadership & Staff   │
└───────────────────┴──────────────────────┘
```

### validate

Validate `resume.yaml` schema and data.

```bash
resume-cli validate
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
- `withdrawn` - Withrew application

### analyze

Show application tracking analytics.

```bash
resume-cli analyze
```

Output:

```
Application Statistics

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric             ┃ Value     ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Applications │ 25        │
│ Applied            │ 20        │
│ Interviews         │ 8         │
│ Offers             │ 3         │
│ Response Rate      │ 32.0%     │
└────────────────────┴───────────┘
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
Backend & DevOps specialization. Emphasizes:
- Backend technologies
- Cloud infrastructure
- Databases
- APIs and scalability

### v1.2.0-ml_ai
ML/AI specialization. Emphasizes:
- AI/ML frameworks
- Data engineering
- Model deployment
- Python and PyTorch

### v1.3.0-fullstack
Full-stack specialization. Emphasizes:
- Frontend and backend balance
- Modern web frameworks
- End-to-end development

### v1.4.0-devops
DevOps & Infrastructure specialization. Emphasizes:
- Kubernetes and Docker
- CI/CD pipelines
- AWS/cloud platforms
- Infrastructure as code

### v1.5.0-leadership
Leadership & Technical Staff. Emphasizes:
- Architecture and design
- Mentoring and team leadership
- Technical strategy
- High-impact projects

## AI-Powered Generation

### Setup

1. Install AI dependencies:
   ```bash
   pip install -e ".[ai]"
   ```

2. Set API key:

   **For Claude (Anthropic):**
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

   **For OpenAI:**
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

3. Configure provider in `config/default.yaml`:
   ```yaml
   ai:
     provider: anthropic  # or openai
     model: claude-3-5-sonnet-20241022
   ```

### Usage

```bash
# Generate with AI customization
resume-cli generate --ai --job-desc job-posting.txt

# AI will:
# 1. Extract key requirements from job description
# 2. Reorder bullets to emphasize relevant experience
# 3. Highlight matching skills
# 4. Keep all content truthful (no fake experience)
```

### Fallback

If AI generation fails, the system automatically falls back to template-based generation (configurable).

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

tracking:
  enabled: true
  csv_path: tracking/resume_experiment.csv

github:
  username: your_username
  sync_months: 3
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
│   ├── integrations/        # Tracking, GitHub, etc.
│   └── utils/               # YAML parser, schema, config
├── templates/               # Jinja2 templates
│   ├── resume_md.j2
│   ├── resume_tex.j2
│   └── email_md.j2
├── config/                  # Configuration files
│   ├── default.yaml
│   └── variants.yaml
├── output/                  # Generated resumes
├── tracking/                # Application tracking CSV
├── requirements.txt         # Python dependencies
└── setup.py                # Package installation
```

## Migration from Old System

The new CLI consolidates:
- Old resume files → `resume.yaml`
- `resume_generator/` → `cli/generators/`
- `tracking/` → Integrated into `cli/integrations/`
- `gh-resume-sync.sh` → `resume-cli sync-github`

**Backward compatibility:** Old files are preserved. Run both systems in parallel during transition.

## Troubleshooting

### "resume.yaml not found"
Run `resume-cli init --from-existing` to create from existing files.

### "anthropic package not installed"
Install AI dependencies: `pip install -e ".[ai]"`

### "ANTHROPIC_API_KEY not set"
Set environment variable: `export ANTHROPIC_API_KEY=your_key`

### "PDF compilation failed"
Install LaTeX tools (see PDF Generation section above).

### "gh command not found"
Install GitHub CLI: https://cli.github.com/

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

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
- Check existing documentation in `docs/`
- Review `tracking/` for application history
- Run `resume-cli validate` to check for errors
