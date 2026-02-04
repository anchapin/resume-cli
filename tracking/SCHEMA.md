# Application Tracking Schema

**File**: `resume_experiment.csv`
**Purpose**: Track all job applications with resume version used to enable A/B testing
**Format**: CSV (comma-separated values)

## Column Definitions

| Column | Type | Required | Values | Description |
|--------|------|----------|--------|-------------|
| `resume_version` | string | ✅ Yes | v1.0.0-base, v1.1.0-backend, etc. | Which resume version was used |
| `company` | string | ✅ Yes | Any company name | Company applied to |
| `role` | string | ✅ Yes | Job title | Position applied for |
| `date_applied` | date | ✅ Yes | YYYY-MM-DD format | When application was submitted |
| `response_status` | enum | ✅ Yes | See values below | Current status of application |
| `time_to_response_days` | integer | ✅ Yes | Number (0 if no response) | Days until first response |
| `notes` | text | No | Any notes | Additional context |
| `application_method` | enum | No | See values below | How you applied |
| `job_url` | url | No | Valid URL | Link to job posting |

## Enumerated Values

### response_status
- `no_response` - No response received yet
- `rejected` - Application rejected
- `interview` - Interview scheduled/completed
- `offer` - Received job offer
- `withdrawn` - Withdrew application

### application_method
- `LinkedIn` - Applied via LinkedIn
- `Direct` - Applied via company website
- `Referral` - Employee referral
- `Recruiter` - Through recruiter/headhunter
- `Other` - Any other method

## Usage Examples

### Example 1: New Application
```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,no_response,0,Applied via LinkedIn Easy Apply,LinkedIn,https://linkedin.com/jobs/123
```

### Example 2: Update with Response
```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,interview,5,Phone screen with recruiter,LinkedIn,https://linkedin.com/jobs/123
```

### Example 3: Final Outcome
```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,offer,14,Offer received! Negotiating,LinkedIn,https://linkedin.com/jobs/123
```

## Best Practices

### DO:
✅ Log every application immediately after submitting
✅ Use consistent date format (YYYY-MM-DD)
✅ Update status when you receive responses
✅ Include job URLs for reference
✅ Track time_to_response_days accurately
✅ Use correct resume version from H1 system

### DON'T:
❌ Leave required fields blank
❌ Use inconsistent date formats
❌ Forget to update application status
❌ Mix up resume versions (check VERSIONS.md)

## Data Quality

### Required Fields
All fields except `notes`, `application_method`, and `job_url` are required.

### Validations
- `date_applied` must be a valid date
- `time_to_response_days` must be ≥ 0
- `resume_version` must exist in H1 VERSIONS.md
- `response_status` must be one of the enum values

### Updating Records
When an application status changes:
1. Find the original row
2. Update `response_status`
3. Update `time_to_response_days`
4. Add update notes to `notes` field

## Integration

### With H1 (Versioned Resumes)
- `resume_version` field links to H1's VERSIONS.md
- Enables analysis of which versions perform best

### With H3 (Targeted Variants)
- Track which variants get more interviews
- Identify high-performing specializations

### With H4 (AI Pipeline)
- Track AI-generated resume performance
- Compare AI vs. manual customization

## Privacy Note

This file contains personal job search data. Do NOT commit to public version control. Consider adding to `.gitignore` if initializing a git repository.
