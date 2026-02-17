## Summary

Integrate the resume-pdf-lib package into resume-cli for shared PDF generation functionality.

## Changes

- Add resume-pdf-lib package to resume-cli
- Update TemplateGenerator to optionally use resume-pdf-lib for PDF generation
- Add methods for generating PDFs using the shared library:
  - `get_pdf_generator()` - Get a PDFGenerator instance
  - `generate_pdf_with_resume_pdf_lib()` - Generate PDF using resume-pdf-lib
  - `_prepare_json_resume_format()` - Convert YAML data to JSON Resume format
- Add support for JSON Resume format conversion
- Add tests for resume-pdf-lib

## Benefits

- Single source of truth for PDF generation
- Consistent PDF output across both applications
- Easier maintenance - single place to update
- Backward compatible - falls back to existing PDF generation if resume-pdf-lib is not available

## Related

- Issue #127: Create resume-pdf-lib package structure
- Issue #129: Publish resume-pdf-lib to production PyPI (depends on this)
