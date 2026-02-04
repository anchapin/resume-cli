# Resume CLI - Quick Reference

## Installation

```bash
cd /home/alexc/Documents/job_hunt
pip install -e .
```

For AI support:
```bash
pip install -e ".[ai]"
export ANTHROPIC_API_KEY=your_key_here
```

## Common Commands

```bash
# List variants
resume-cli variants

# Generate resume
resume-cli generate -v v1.0.0-base -f md
resume-cli generate -v v1.1.0-backend -f pdf
resume-cli generate -v v1.2.0-ml_ai -f md

# Validate data
resume-cli validate

# Track applications
resume-cli apply Company applied -r "Job Title"
resume-cli apply Company interview -v v1.1.0-backend

# Analytics
resume-cli analyze

# Sync GitHub projects
resume-cli sync-github --months 3
```

## File Structure

```
job_hunt/
├── resume.yaml          # Edit this file to update resume
├── cli/                 # CLI code
├── templates/           # Jinja2 templates
├── config/              # Configuration
├── output/              # Generated resumes
└── tracking/            # Application tracking CSV
```

## Updating Resume

1. Edit `resume.yaml`
2. Run `resume-cli validate` to check for errors
3. Run `resume-cli generate -v VARIANT -f FORMAT` to generate

## Variants

- `v1.0.0-base` - General software engineering
- `v1.1.0-backend` - Backend & DevOps
- `v1.2.0-ml_ai` - ML/AI specialization
- `v1.3.0-fullstack` - Full-stack web
- `v1.4.0-devops` - DevOps & Infrastructure
- `v1.5.0-leadership` - Leadership & Staff

## Status Values for Tracking

- `applied` - Application submitted
- `interview` - Interview scheduled
- `offer` - Offer received
- `rejected` - Application rejected
- `withdrawn` - Withdrew application
