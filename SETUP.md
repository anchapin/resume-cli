# Resume CLI Local Development Setup

A comprehensive guide to setting up and using the Resume CLI locally for development and production use.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Verify Installation](#verify-installation)
- [Development Workflow](#development-workflow)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## System Requirements

- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12 (tested in CI)
  - Check with `python3 --version`
- **LaTeX** (optional, for PDF generation):
  - **Ubuntu/Debian**: `sudo apt-get install texlive-full`
  - **Fedora/RHEL**: `sudo dnf install texlive-scheme-full`
  - **macOS**: `brew install mactex`
  - Verify: `pdflatex --version`
- **GitHub CLI** (optional, for `sync-github` command):
  - Install from https://cli.github.com/
- **Git**: For version control

## Quick Start

```bash
# 1. Clone/navigate to project
cd resume-cli

# 2. Install resume-cli
make install

# 3. Set up resume data
cp resume.example.yaml resume.yaml

# 4. Validate your data
make validate

# 5. Generate first resume
make generate

# 6. View available variants
make variants
```

## Detailed Installation

### Step 1: Prerequisites Check

```bash
# Check Python (need 3.8+)
python3 --version

# Check Git
git --version

# (Optional) Check LaTeX for PDF generation
pdflatex --version

# (Optional) Check GitHub CLI for GitHub integration
gh --version
```

### Step 2: Install Resume CLI

**Basic installation** (template-based generation only):
```bash
make install
# Or manually: pip install -e .
```

**With AI support** (Claude, OpenAI, or Gemini):
```bash
make install-ai
# Or manually: pip install -e ".[ai]"
```

**With development tools** (testing, linting):
```bash
make install-dev
# Or manually: pip install -e ".[dev]"
```

### Step 3: Configure Environment

Create `.env` file for API keys (if using AI):

```bash
cp .env.template .env
```

Edit `.env` with your keys:
```bash
# For Claude (Anthropic)
ANTHROPIC_API_KEY=sk-ant-...

# For OpenAI
OPENAI_API_KEY=sk-...

# For Gemini
GEMINI_API_KEY=...
```

### Step 4: Set Up Resume Data

```bash
# Copy example resume
cp resume.example.yaml resume.yaml

# Edit with your information
nano resume.yaml
```

See `YAML_SCHEMA.md` for detailed schema documentation.

## Verify Installation

### Quick Health Check

```bash
# Check installation
resume-cli --help

# Validate resume data
make validate

# View available variants
make variants

# Check dependencies
make check-deps

# Check configuration files
make check-config
```

### Expected Output

```bash
$ resume-cli --help
Usage: resume-cli [OPTIONS] COMMAND [ARGS]...

  Resume CLI System - AI-powered resume generation from YAML

Options:
  --help  Show this message and exit.

Commands:
  generate          Generate a resume from template or AI
  validate          Validate resume.yaml schema
  variants          List all available resume variants
  ats-check         Check ATS compatibility score
  generate-package  Generate application package (resume + cover letter)
  apply             Log a job application
  analyze           View application analytics
  ...
```

## Development Workflow

### Common Development Tasks

```bash
# Validate resume changes before generating
make validate

# Generate resume to preview changes
make generate

# Generate specific variant and format
resume-cli generate -v v1.1.0-backend -f pdf

# Preview without saving
resume-cli generate -v v1.1.0-ml_ai --no-save | head -50

# Generate with AI customization for a job
resume-cli generate --ai --job-desc job-posting.txt

# Generate complete application package
resume-cli generate-package --job-desc job.txt --company "Acme Corp"

# Check ATS compatibility
resume-cli ats-check --job-desc job.txt -v v1.1.0-backend

# Track job applications
resume-cli apply "Acme Corp" applied -r "Senior Engineer"

# View application statistics
resume-cli analyze

# Sync GitHub projects (requires GitHub CLI)
resume-cli sync-github --months 3
```

### Hot Reload for Development

When modifying templates or code:

1. **Template changes** (templates/*.j2):
   - Templates are reloaded on each generation
   - No restart needed

2. **Python code changes** (cli/):
   - If using `pip install -e .`, changes take effect immediately
   - For some changes, reinstall: `pip install -e .`

3. **Configuration changes** (config/default.yaml):
   - Config is loaded on command execution
   - No restart needed

### Testing Your Changes

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test file
pytest tests/test_yaml_parser.py -v

# Run tests matching a pattern
pytest -k "variant" -v
```

### Code Quality

```bash
# Check code style
make lint

# Format code
make format
```

## Common Commands

### Working with Resumes

```bash
# Generate base resume as Markdown
resume-cli generate -v v1.0.0-base -f md

# Generate backend variant as PDF
resume-cli generate -v v1.1.0-backend -f pdf

# Save to custom location
resume-cli generate -f pdf -o my-resume.pdf

# Preview before saving
resume-cli generate -v v1.2.0-ml_ai --no-save | less

# List all variants
resume-cli variants
```

### AI-Powered Generation

```bash
# AI-customized resume for a job
resume-cli generate --ai --job-desc job-posting.txt

# Generate with AI Judge (multiple generations)
resume-cli generate --ai --job-desc job.txt --judge

# Combine variants and AI
resume-cli generate -v v1.1.0-backend --ai --job-desc job.txt
```

### Application Packages (Resume + Cover Letter)

```bash
# Interactive mode (asks questions)
resume-cli generate-package --job-desc job.txt --variant v1.1.0-backend

# Non-interactive mode (auto-generates)
resume-cli generate-package --job-desc job.txt --company "Acme" --non-interactive

# With GitHub project auto-selection
resume-cli generate-package --job-desc job.txt --include-github-projects

# Custom output directory
resume-cli generate-package --job-desc job.txt --output-dir ./my-packages
```

### ATS Optimization

```bash
# Check ATS score
resume-cli ats-check --job-desc job.txt

# Save report as JSON
resume-cli ats-check --job-desc job.txt --output ats-report.json

# Check specific variant
resume-cli ats-check -v v1.1.0-backend --job-desc job.txt
```

### Application Tracking

```bash
# Log an application
resume-cli apply "Acme Corp" applied -r "Senior Engineer"

# Update application status
resume-cli apply "Acme Corp" interview

# View analytics
resume-cli analyze

# View analytics for specific status
resume-cli analyze --status interview

# Export to CSV
resume-cli analyze --export applications.csv
```

### GitHub Integration

```bash
# Sync GitHub projects (requires GitHub CLI)
resume-cli sync-github --months 3

# Sync and update resume.yaml
resume-cli sync-github --months 6 --update-resume

# Categorize specific repo
resume-cli sync-github --username my-username
```

### LinkedIn Integration

```bash
# Import LinkedIn profile data
resume-cli import-linkedin

# Export resume to LinkedIn format
resume-cli export-linkedin
```

## Troubleshooting

### "resume-cli: command not found"

Ensure the package is installed:

```bash
# Check installation
pip list | grep resume

# Reinstall
pip install -e .

# If still not found, check pip PATH
which pip
which python3
```

### "resume.yaml not found"

```bash
# Copy example
cp resume.example.yaml resume.yaml

# Or create from existing resume
resume-cli init --from-existing
```

### "anthropic package not installed"

```bash
# Install AI support
make install-ai
# Or: pip install -e ".[ai]"
```

### "ANTHROPIC_API_KEY not set"

```bash
# Create .env file
cp .env.template .env

# Add your key
echo "ANTHROPIC_API_KEY=sk-..." >> .env

# Or set environment variable
export ANTHROPIC_API_KEY=sk-...
```

### "PDF compilation failed"

PDF generation requires LaTeX. Install it:

```bash
# Ubuntu/Debian
sudo apt-get install texlive-full

# Fedora/RHEL
sudo dnf install texlive-scheme-full

# macOS
brew install mactex

# Verify
pdflatex --version
```

### "gh command not found"

GitHub integration requires GitHub CLI:

```bash
# Install from https://cli.github.com/
# Or use your package manager

# Ubuntu/Debian
sudo apt-get install gh

# Fedora
sudo dnf install gh

# macOS
brew install gh

# Verify
gh --version
```

### Validation Errors

Run validation to check your resume.yaml:

```bash
make validate

# Or manually
resume-cli validate
```

This checks:
- Required fields present
- Date format correct (YYYY-MM)
- Email format valid
- Skill sections exist

### YAML Parse Errors

If resume.yaml won't parse:

1. **Check YAML syntax**: https://yamllint.com/
2. **Ensure proper indentation** (2 spaces, not tabs)
3. **Quote strings with special characters**
4. **Check for duplicate keys**

Example valid YAML:
```yaml
contact:
  name: "John Doe"
  email: "john@example.com"
  phone: "+1 (555) 123-4567"

experience:
  - company: "Tech Corp"
    title: "Senior Engineer"
    start_date: "2023-01"
    end_date: null
```

### AI Generation Issues

```bash
# Test API connection
python -c "from anthropic import Anthropic; Anthropic().messages.create(...)"

# Check API key
echo $ANTHROPIC_API_KEY

# Check rate limits
# If rate limited, try again after a minute

# Try different AI provider
resume-cli generate --ai --job-desc job.txt --provider openai
```

### Template Errors

If generated resume has formatting issues:

1. **Check template files** in `templates/`
2. **Verify template context** - variables must exist in resume.yaml
3. **Test template rendering**:
   ```bash
   resume-cli generate -v v1.0.0-base --no-save | head -100
   ```

### Performance Issues

```bash
# AI generation can be slow (10-30 seconds)
# PDF compilation can be slow (5-10 seconds)

# To speed up:
# - Use Markdown format instead of PDF
# - Disable AI Judge (single generation)
# - Use faster AI provider (GPT-4o-mini instead of GPT-4o)
```

## Advanced Usage

### Custom Variants

Edit `resume.yaml` to add new variants:

```yaml
variants:
  v1.3.0-cloud:
    description: "Cloud/DevOps focused resume"
    summary_key: cloud
    skill_sections: [languages, cloud, devops]
    max_bullets_per_job: 5
    emphasize_keywords:
      - Kubernetes
      - Docker
      - AWS
      - GCP
      - Terraform
```

Then generate:
```bash
resume-cli generate -v v1.3.0-cloud -f pdf
```

### Custom Templates

Create a new Jinja2 template:

```bash
# Create template file
cat > templates/resume_html.j2 << 'EOF'
<!DOCTYPE html>
<html>
  <head>
    <title>{{ contact.name }} - Resume</title>
  </head>
  <body>
    <h1>{{ contact.name }}</h1>
    <p>{{ contact.email }}</p>
    <!-- Add your template -->
  </body>
</html>
EOF
```

Use it:
```bash
resume-cli generate -v v1.0.0-base -f html
```

### Batch Generation

```bash
#!/bin/bash
# Generate all variants as PDF

for variant in $(resume-cli variants | grep "^v"); do
  echo "Generating $variant..."
  resume-cli generate -v "$variant" -f pdf -o "output/${variant}.pdf"
done
```

### Integration with Other Tools

**Parse generated resume for data extraction**:
```bash
resume-cli generate -v v1.0.0-base --no-save | python parse_resume.py
```

**Use in CI/CD pipeline**:
```yaml
# .github/workflows/validate.yml
- name: Validate resumes
  run: |
    make install
    make validate
```

## Project Structure

```
resume-cli/
├── cli/                         # Main CLI package
│   ├── main.py                  # Click CLI entry point
│   ├── commands/                # Command implementations
│   ├── generators/              # Template and AI generators
│   ├── integrations/            # GitHub, LinkedIn, tracking
│   └── utils/                   # YAML parser, config, validation
├── resume_pdf_lib/              # PDF generation library
├── templates/                   # Jinja2 templates
│   ├── resume_md.j2
│   ├── resume_tex.j2
│   ├── email_md.j2
│   └── cover_letter_md.j2
├── config/                      # Configuration
│   ├── default.yaml
│   └── variants.yaml
├── tests/                       # Test suite
├── output/                      # Generated resumes (gitignored)
├── tracking/                    # Application tracking (gitignored)
├── resume.example.yaml          # Example resume data
├── .env.template                # Environment template
├── Makefile                      # Development commands
├── SETUP.md                      # This file
├── CLAUDE.md                     # Developer documentation
├── pyproject.toml              # Package configuration
└── requirements.txt            # Dependencies
```

## Next Steps

1. **Set up resume data**: `cp resume.example.yaml resume.yaml`
2. **Edit with your information**: `nano resume.yaml`
3. **Validate**: `make validate`
4. **Generate**: `make generate`
5. **Optional**: Install AI support for advanced features: `make install-ai`
6. **Explore**: See `CLAUDE.md` for architecture and development details

## Getting Help

- **Command help**: `resume-cli --help` or `resume-cli COMMAND --help`
- **Architecture**: See `CLAUDE.md` for detailed technical documentation
- **API**: `resume-cli generate --help` for resume generation options
- **Issues**: Check GitHub issues or create a new one

## Resources

- [CLAUDE.md](CLAUDE.md) - Developer guidelines and architecture
- [README.md](README.md) - Project overview and features
- [resume.example.yaml](resume.example.yaml) - Example resume structure
- [config/default.yaml](config/default.yaml) - Configuration options
- [templates/](templates/) - Jinja2 template examples
