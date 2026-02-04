# H2: A/B Testing Framework - Application Tracking System

**Status**: ✅ IMPLEMENTED
**Date**: 2025-01-23
**R_eff**: 0.90 (HIGH CONFIDENCE)

## Overview

This directory implements **H2: A/B Testing Framework** from the FPF decision process. It tracks job applications and analyzes which resume versions perform best.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install pandas directly:
```bash
pip install pandas
```

### 2. Log Your First Application

Edit `resume_experiment.csv` and add a row:

```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,no_response,0,Applied via LinkedIn,LinkedIn,https://linkedin.com/jobs/123
```

### 3. Run Analysis

```bash
python tracking/analyze_performance.py
```

## Directory Structure

```
tracking/
├── README.md                 # This file
├── SCHEMA.md                 # Data schema documentation
├── resume_experiment.csv     # Your application data
├── template.csv              # Template for new entries
├── analyze_performance.py    # Analysis script
└── requirements.txt          # Python dependencies
```

## How It Works

### Data Collection

Every time you apply for a job, log it in `resume_experiment.csv` with:

- **Which resume version** you used (links to H1 system)
- **Company and role** you applied for
- **Date applied**
- **Response status** (update as you hear back)
- **Time to response** (days until first response)
- **Application method** (LinkedIn, referral, etc.)
- **Job URL** (for reference)

### Analysis

Run the analyzer to get insights:

```bash
# Full report
python tracking/analyze_performance.py

# Analyze specific resume version
python tracking/analyze_performance.py --version v1.0.0-base

# Use different CSV file
python tracking/analyze_performance.py --csv path/to/data.csv
```

### What You'll Learn

The analyzer tells you:

- 📊 **Response rates** by resume version
- 📞 **Interview rates** by resume version
- 🎉 **Offer rates** by resume version
- ⏱️ **Average time to response** by version
- 📮 **Best application methods** (LinkedIn vs. referral vs. direct)
- 💡 **Which versions to retire** (low performers)
- 🏆 **Which versions to use more** (top performers)

## CSV Schema

See `SCHEMA.md` for complete schema documentation.

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `resume_version` | Which resume from H1 | v1.0.0-base |
| `company` | Company name | Google |
| `role` | Job title | Software Engineer |
| `date_applied` | When you applied | 2025-01-23 |
| `response_status` | Current status | interview |
| `time_to_response_days` | Days until response | 7 |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `notes` | Additional context | Phone screen scheduled |
| `application_method` | How you applied | LinkedIn |
| `job_url` | Link to posting | https://... |

## Response Status Values

- `no_response` - Haven't heard back yet
- `rejected` - Application rejected
- `interview` - Interview scheduled or completed
- `offer` - Received job offer
- `withdrawn` - You withdrew from consideration

## Example Workflow

### Day 1: Apply for Jobs

```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,no_response,0,Applied via LinkedIn,LinkedIn,https://linkedin.com/jobs/123
v1.0.0-base,Meta,Backend Engineer,2025-01-23,no_response,0,Referral from John,Referral,
v1.1.0-backend,Stripe,API Developer,2025-01-23,no_response,0,Applied via careers page,Direct,https://stripe.com/jobs
```

### Day 7: Get Responses

Update the CSV:

```csv
v1.0.0-base,Google,Software Engineer,2025-01-23,interview,7,Phone screen with recruiter,LinkedIn,https://linkedin.com/jobs/123
v1.0.0-base,Meta,Backend Engineer,2025-01-23,rejected,5,Automated rejection,Referral,
v1.1.0-backend,Stripe,API Developer,2025-01-23,no_response,0,Applied via careers page,Direct,https://stripe.com/jobs
```

### Run Analysis

```bash
$ python tracking/analyze_performance.py

======================================================================
                      📊 RESUME PERFORMANCE ANALYSIS
======================================================================

📈 Overview:
   Total Applications: 3
   Resume Versions: 2
   Date Range: 2025-01-23 to 2025-01-23

📬 Overall Response Rate: 66.7% (2/3)

🎯 Performance by Resume Version:

   v1.0.0-base:
      Applications:    2
      Response Rate:   100.0%
      Interview Rate:  50.0% (1)
      Offer Rate:      0.0% (0)
      Rejected:        1
      No Response:     0
      Avg Response Time: 6.0 days

   v1.1.0-backend:
      Applications:    1
      Response Rate:   0.0%
      Interview Rate:  0.0% (0)
      Offer Rate:      0.0% (0)
      Rejected:        0
      No Response:     1
      Avg Response Time: 0.0 days
```

## Best Practices

### DO:
✅ Log applications immediately after submitting
✅ Update status when you receive responses
✅ Track time_to_response_days accurately
✅ Use correct resume version from H1
✅ Run analysis monthly to identify trends
✅ Include job URLs for easy reference

### DON'T:
❌ Forget to log applications (data gaps = bad analysis)
❌ Use inconsistent date formats (stick to YYYY-MM-DD)
❌ Leave required fields blank
❌ Mix up resume versions
❌ Stop updating old applications (status changes matter)

## Analysis Frequency

### Weekly
- Update response statuses for recent applications
- Quick check: any new interviews or offers?

### Monthly
- Run full analysis: `python tracking/analyze_performance.py`
- Review which versions perform best
- Identify underperforming versions (consider retiring)

### Quarterly
- Deep dive into trends
- Decide if new resume variants are needed
- Update H1 VERSIONS.md based on findings

## Integration with FPF System

### H1 (Versioned Resumes)
- Tracks which resume version was used for each application
- Enables version-to-performance mapping
- Provides data for retiring low-performing versions

### H3 (Targeted Variants)
- Compare backend variant vs. general resume
- Identify which specializations perform best
- Validate role-targeting strategy

### H4 (AI Pipeline)
- Track AI-generated resume performance
- Compare AI vs. manual customization
- Measure ROI of automation

## Privacy Note

⚠️ **This file contains personal job search data.**

Do NOT commit to public version control. Add to `.gitignore`:

```gitignore
tracking/resume_experiment.csv
```

## Troubleshooting

### "No module named 'pandas'"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "CSV file not found"

Copy the template:
```bash
cp tracking/template.csv tracking/resume_experiment.csv
```

### "No application data found"

Add your first application to the CSV.

### Analysis shows "Need more data"

You need at least 3-5 applications per version for meaningful analysis. Keep applying!

## Success Metrics

After 50+ applications, you should be able to:

- ✅ Identify top-performing resume version
- ✅ Know which application methods work best
- ✅ See clear response rate differences
- ✅ Make data-driven decisions about which versions to use
- ✅ Retire underperforming variants

## Next Steps

1. **Start tracking**: Log every application going forward
2. **Build habits**: Update CSV immediately after applying
3. **Run analysis**: Check performance monthly
4. **Iterate**: Use data to improve resume strategy

---

**Built as part of**: Full-stack resume optimization system (H1+H2+H3+H4)
**Documentation**: `../H2-IMPLEMENTATION.md`
**Design rationale**: `../.quint/decisions/DRR-2025-01-23-resume-optimization-full-stack.md`
