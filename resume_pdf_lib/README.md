# resume-pdf-lib

Shared Python library for PDF resume generation using LaTeX templates.

## Installation

```bash
pip install resume-pdf-lib
```

## Usage

```python
from resume_pdf_lib import PDFGenerator

generator = PDFGenerator(templates_dir="/path/to/templates")
pdf_bytes = generator.generate_pdf(resume_data, variant="modern")
```

## Requirements

- Python 3.9+
- jinja2>=3.0.0
- markupsafe>=2.0.0
- LaTeX distribution (TeX Live, MacTeX, or MiKTeX)
