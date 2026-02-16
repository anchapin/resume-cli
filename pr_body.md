## Summary

Improves error messages throughout the CLI to provide clear, actionable guidance as described in issue #9.

## Changes

- Enhanced ValidationError class with guidance parameter
- Added ERROR_GUIDANCE dictionary with What to do instructions
- Improved validation output with actionable guidance

## Coverage

- Missing contact fields (name, phone, email)
- Invalid email format
- Missing required sections (experience, education, skills)
- File not found errors
- YAML parsing errors

## Related Issues

- Resolves #9 (Improve error messages with actionable guidance)
