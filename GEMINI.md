# Resume CLI System - Gemini Context

This document provides context for Gemini when working with the Resume CLI System.

## Project Overview

The **Resume CLI System** is a Python-based command-line tool designed to generate job-specific resumes and cover letters from a single YAML source of truth (`resume.yaml`). It combines fast template-based generation (Jinja2) with optional AI-powered customization (Claude/OpenAI).

### Key Features
*   **Single Source of Truth:** All data resides in `resume.yaml`.
*   **Multi-Format:** Generates Markdown, LaTeX, and PDF (via LaTeX/Pandoc).
*   **AI Customization:** Tailors resumes and generates cover letters based on job descriptions.
*   **Application Tracking:** Built-in command to log and analyze job applications.
*   **GitHub Integration:** Syncs projects from GitHub to the resume data.

## Architecture

### Directory Structure
*   `cli/`: Main package source code.
    *   `main.py`: CLI entry point using `click`.
    *   `commands/`: Implementation of specific commands (e.g., `init`).
    *   `generators/`: Core logic for generation.
        *   `template.py`: Jinja2 template rendering.
        *   `ai_generator.py`: AI integration (Claude/OpenAI) for resume tailoring.
        *   `cover_letter_generator.py`: AI logic for cover letters.
    *   `integrations/`: External services (GitHub, CSV tracking).
    *   `utils/`: Helpers for config, YAML parsing, and schema validation.
*   `templates/`: Jinja2 templates (`.j2`) for resumes and emails.
*   `config/`: Configuration files (`default.yaml`, `variants.yaml`).
*   `resume.yaml`: User's resume data (created via `init`).
*   `output/`: Directory where generated files are saved.

### Data Flow
1.  **Input:** User runs a command (e.g., `resume-cli generate`).
2.  **Parsing:** `ResumeYAML` reads `resume.yaml`.
3.  **Processing:**
    *   **Template Mode:** `TemplateGenerator` filters data based on the selected `variant` and renders a Jinja2 template.
    *   **AI Mode:** `AIGenerator` takes the base template output and uses an LLM to rewrite/reorder content based on the provided job description.
4.  **Output:** Files are written to the `output/` directory (or printed to stdout).

## Building and Running

### Installation
The project is a Python package managed with `setup.py`.

```bash
# Basic install
pip install -e .

# Install with AI dependencies (anthropic, openai)
pip install -e ".[ai]"
```

### Key Commands

**1. Generation:**
```bash
# Basic template generation
resume-cli generate -v v1.0.0-base -f md

# AI-tailored generation (requires API key)
resume-cli generate --ai --job-desc job_posting.txt -v v1.1.0-backend

# Generate full package (Resume + Cover Letter)
resume-cli generate-package --job-desc job_posting.txt --company "Acme Corp"
```

**2. Management:**
```bash
# Initialize/Update resume.yaml
resume-cli init --from-existing

# Validate schema
resume-cli validate

# List variants
resume-cli variants
```

**3. Tracking:**
```bash
# Log an application
resume-cli apply "Company Name" applied -r "Role"

# View statistics
resume-cli analyze
```

### Environment Variables
*   `ANTHROPIC_API_KEY`: Required for Claude-based AI features.
*   `OPENAI_API_KEY`: Required for OpenAI-based AI features.

## Development Conventions

*   **CLI Framework:** Uses `click` for command definitions and argument parsing.
*   **Output:** Uses `rich` for formatted terminal output (tables, colors).
*   **Testing:** Uses `pytest` (currently configured but tests may be sparse).
*   **Style:** Follows standard Python PEP 8 conventions.
*   **Safety:** AI generation is designed to be truthful—it rewrites existing content but should not hallucinate new experiences.

## Common Tasks for AI Assistant

*   **Modifying Templates:** Edit `.j2` files in `templates/`. Remember to check `cli/generators/template.py` if new context variables are needed.
*   **Adding Variants:** Edit `resume.yaml` to add new variant definitions under `variants:` and corresponding summaries.
*   **Debugging AI:** Check `cli/generators/ai_generator.py` for prompt logic. The system uses an "AI Judge" pattern to evaluate multiple drafts.
