# resume-pdf-lib

Shared Python library for PDF resume generation using LaTeX templates.

## Features

- **LaTeX Template Rendering**: Generate professional PDF resumes using Jinja2 templates
- **Multiple Format Support**: Works with both YAML-based (resume-cli) and JSON Resume formats
- **Template Variants**: Support for multiple template styles (modern, academic, technical, etc.)
- **Custom Filters**: Built-in LaTeX escaping and title case filters
- **Easy Integration**: Simple API for generating PDFs from structured data

## Installation

```bash
pip install resume-pdf-lib
```

## Usage

### Basic Usage

```python
from resume_pdf_lib import PDFGenerator

# Initialize generator (uses built-in templates)
generator = PDFGenerator()

# Prepare resume data (supports both YAML and JSON Resume formats)
resume_data = {
    "basics": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1 234 567 8900",
        "summary": "Experienced software engineer...",
    },
    "work": [
        {
            "company": "Tech Corp",
            "position": "Senior Developer",
            "startDate": "2020-01",
            "endDate": "Present",
            "highlights": [
                "Led development of microservices architecture",
                "Improved system performance by 40%",
            ]
        }
    ],
    "education": [...],
    "skills": [...],
}

# Generate PDF
pdf_bytes = generator.generate_pdf(resume_data, variant="modern")

# Or save to file
generator.generate_pdf(resume_data, variant="modern", output_path="resume.pdf")
```

### Using with Different Data Formats

#### JSON Resume Format

```python
resume_data = {
    "basics": {
        "name": "John Doe",
        "email": "john@example.com",
        ...
    },
    "work": [...],
    "education": [...],
    ...
}
```

#### YAML Format (resume-cli style)

```python
resume_data = {
    "contact": {
        "name": "John Doe",
        "email": "john@example.com",
        ...
    },
    "summary": "Experienced software engineer...",
    "experience": [...],
    "education": [...],
    "skills": {...},
}
```

### Listing Available Templates

```python
variants = generator.list_variants()
print(variants)  # ['base', 'modern', 'technical', ...]
```

## Requirements

- Python 3.9+
- jinja2>=3.0.0
- markupsafe>=2.0.0
- LaTeX distribution (TeX Live, MacTeX, or MiKTeX) for PDF generation

## Development

```bash
# Clone the repository
git clone https://github.com/anchapin/resume-cli.git
cd resume-cli/resume_pdf_lib

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black resume_pdf_lib/ tests/

# Type checking
mypy resume_pdf_lib/
```

## License

MIT
