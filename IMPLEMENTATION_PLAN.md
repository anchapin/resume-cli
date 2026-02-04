# Implementation Plan: Unified Resume + Cover Letter Generation

## Overview

Add a new CLI command that generates both a targeted resume and a personalized cover letter for a specific job description. The AI will be able to ask follow-up questions when needed to create a more compelling cover letter.

## Current State

- **AI Generator** (`cli/generators/ai_generator.py`): Functional, supports Claude/OpenAI
- **Email Template** (`templates/email_md.j2`): Exists, can be adapted for cover letters
- **Generate Command**: Supports `--ai` and `--job-desc` flags for resume generation
- **No cover letter generation**: Currently no dedicated cover letter functionality

## Design Decisions

### 1. Command Structure

**Option A**: Add `--cover-letter` flag to existing `generate` command
- Pros: Simple, unified workflow
- Cons: Couples resume and cover letter generation

**Option B**: Create new `generate-package` command (RECOMMENDED)
```bash
resume-cli generate-package --job-desc job.txt --variant v1.1.0-backend
```
- Pros: Clean separation, makes intent explicit, allows for package-specific options
- Cons: Additional command to learn

### 2. AI Question/Answer Flow

The AI should ask follow-up questions for cover letter generation when it lacks context. Two approaches:

**Interactive Mode** (default):
```bash
resume-cli generate-package --job-desc job.txt
# AI asks: "What excites you about this role?"
# User answers
# AI asks: "Do you have a connection at the company?"
# User answers (or skip)
# Generation completes
```

**Non-Interactive Mode** (smart guesses enabled):
```bash
resume-cli generate-package --job-desc job.txt --non-interactive
# Uses AI-generated smart guesses for optional questions
# No prompts, fully automated
```

### 3. Output Structure

**DECIDED**: Subdirectories per application
```
output/
  └── {company}-{date}/
      ├── resume.{ext}
      ├── resume.pdf (if ext != pdf)
      ├── cover-letter.md
      └── cover-letter.pdf
```

**Cover Letter Formats**: Both Markdown and PDF will be generated (user decision)

## Implementation Plan

### Phase 1: Cover Letter Template and Generator

**Key Requirements**:
- Generate cover letter in Markdown format
- Compile to PDF (reuse existing PDF compilation from `TemplateGenerator`)
- Support custom template paths (future enhancement)

#### 1.1 Create Cover Letter Template
**File**: `templates/cover_letter_md.j2`

```jinja2
# {{ position_name }} Application - {{ contact.name }}

{{ contact.name }}
{{ contact.email }} | {{ contact.phone }}
{% if contact.urls.linkedin %}{{ contact.urls.linkedin }}{% endif %}
{% if contact.urls.github %}{{ contact.urls.github }}{% endif %}

{{ current_date }}

{{ hiring_manager_name|default('Hiring Manager') }}
{{ company_name }}
{{ company_address|default('') }}

{{ company_name|default('[Company Name]') }}

Dear {{ hiring_manager_name|default('Hiring Manager') }},

{{ opening_paragraph }}

{{ body_paragraphs }}

{{ closing_paragraph }}

Best regards,

{{ contact.name }}
{% if contact.urls.linkedin %}{{ contact.urls.linkedin }}{% endif %}
{% if contact.urls.github %}{{ contact.urls.github }}{% endif %}
```

#### 1.2 Create Cover Letter Generator Class
**File**: `cli/generators/cover_letter_generator.py`

```python
class CoverLetterGenerator:
    """Generate personalized cover letters with AI."""

    def __init__(self, yaml_path, config):
        self.yaml_handler = ResumeYAML(yaml_path)
        self.config = config
        # Initialize AI client (reuse from AIGenerator)

    def generate_interactive(
        self,
        job_description: str,
        variant: str,
        output_path: Optional[Path] = None,
        non_interactive: bool = False
    ) -> tuple[str, dict]:
        """
        Generate cover letter, asking questions as needed.

        Returns:
            (cover_letter_content, question_answers_dict)
        """

    def _extract_job_details(self, job_desc: str) -> dict:
        """Extract company, position, requirements using AI."""

    def _determine_questions(self, job_details: dict) -> list:
        """Decide what questions to ask based on job + resume gap."""

    def _ask_question(self, question: str) -> str:
        """Prompt user and return answer."""

    def _generate_with_ai(
        self,
        job_details: dict,
        question_answers: dict,
        variant: str
    ) -> str:
        """Generate final cover letter using AI."""
```

### Phase 2: AI Question Determination Logic

#### 2.1 Question Categories

The AI should ask about information not in `resume.yaml`:

| Question Type | Trigger Condition | Example Question |
|--------------|-------------------|------------------|
| Company connection | Job description mentions referral | "Do you know anyone at [Company]?" |
| Motivation | Always (cover letter essential) | "What excites you about this role?" |
| Company-specific knowledge | Company has unique mission/products | "What about [Company]'s mission resonates with you?" |
| Gap addressing | Resume has employment gap | "Would you like to address your career transition?" |
| Relocation | Remote job + different location | "Are you willing to relocate?" |
| Salary expectations | Job mentions salary | "Any salary requirements?" |

#### 2.2 Smart Guesses for Non-Interactive Mode

When `--non-interactive` flag is used, the AI will generate smart guesses instead of prompting:

```python
def _generate_smart_guesses(self, job_details: dict, resume_data: dict) -> dict:
    """Generate AI-based guesses for cover letter questions."""
    # Use AI to infer:
    # - Motivation: Based on job requirements + resume skills alignment
    # - Company alignment: Based on company mission in job description
    # - Connection: Default to "no" (safe assumption)
    return {
        "motivation": ai_generated_motivation,
        "company_alignment": ai_generated_alignment,
        "connection": None  # Skip if no explicit connection
    }
```

#### 2.3 Smart Question Selection

```python
def _determine_questions(self, job_details: dict, resume_data: dict) -> list:
    questions = []

    # Always ask about motivation
    questions.append({
        "key": "motivation",
        "question": f"What specifically excites you about the {job_details['position']} role at {job_details['company']}?",
        "required": True
    })

    # Check for company-specific context needed
    if job_details.get("company_mission"):
        questions.append({
            "key": "company_alignment",
            "question": f"What aspects of {job_details['company']}'s mission resonate with you?",
            "required": False
        })

    # Check if user might have connections
    questions.append({
        "key": "connection",
        "question": f"Do you have any connections at {job_details['company']}? (Press Enter to skip)",
        "required": False
    })

    return questions
```

### Phase 3: Unified Package Command

#### 3.1 New Command: `generate-package`

**File**: `cli/main.py` (add new command)

```python
@cli.command()
@click.option("-v", "--variant", default="v1.0.0-base", help="Resume variant")
@click.option("-f", "--format", type=click.Choice(["md", "tex", "pdf"]), default="md", help="Resume format")
@click.option("--job-desc", type=click.Path(exists=True), required=True, help="Job description file")
@click.option("--company", type=str, help="Company name (overrides extraction from job description)")
@click.option("--non-interactive", is_flag=True, help="Skip questions, use smart defaults")
@click.option("--no-cover-letter", is_flag=True, help="Skip cover letter generation")
@click.option("--output-dir", type=click.Path(), help="Output directory (default: config setting)")
@click.pass_context
def generate_package(ctx, variant, format, job_desc, company, non_interactive,
                    no_cover_letter, output_dir):
    """
    Generate a complete application package: resume + cover letter.

    Output is organized in subdirectories:
        output/{company}-{date}/
            ├── resume.{ext}
            ├── cover-letter.md
            └── cover-letter.pdf

    Example:
        resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend
        resume-cli generate-package --job-desc job.txt --company "Acme Corp" --non-interactive
    """
    yaml_path = ctx.obj["yaml_path"]
    config = ctx.obj["config"]

    job_description = Path(job_desc).read_text()

    console.print("[bold blue]Generating Application Package[/bold blue]")

    # 1. Generate AI-customized resume
    console.print("\n[cyan]Step 1: Generating resume...[/cyan]")
    from .generators.ai_generator import AIGenerator
    resume_gen = AIGenerator(yaml_path, config=config)
    resume_content = resume_gen.generate(
        variant=variant,
        job_description=job_description,
        output_format=format,
        output_path=resume_output_path
    )
    console.print(f"[green]✓[/green] Resume: {resume_output_path}")

    # 2. Generate cover letter
    if not no_cover_letter:
        console.print("\n[cyan]Step 2: Generating cover letter...[/cyan]")
        from .generators.cover_letter_generator import CoverLetterGenerator
        cl_gen = CoverLetterGenerator(yaml_path, config=config)

        if non_interactive:
            cover_letter, qa_dict = cl_gen.generate_non_interactive(
                job_description=job_description,
                variant=variant,
                output_path=cover_letter_output_path
            )
        else:
            cover_letter, qa_dict = cl_gen.generate_interactive(
                job_description=job_description,
                variant=variant,
                output_path=cover_letter_output_path
            )

        console.print(f"[green]✓[/green] Cover letter: {cover_letter_output_path}")

    console.print("\n[bold green]Application package complete![/bold green]")
```

### Phase 4: Configuration Updates

#### 4.1 Add Cover Letter Settings to Config

**File**: `config/default.yaml`

```yaml
# ... existing config ...

cover_letter:
  enabled: true
  template: cover_letter_md.j2
  output_directory: output
  formats: [md, pdf]  # Generate both formats
  default_questions:
    - motivation
    - connection
  optional_questions:
    - company_alignment
    - relocation
    - salary
  # Non-interactive mode: smart guesses enabled
  smart_guesses: true
  # AI settings (inherit from ai: section, can override)
  tone: professional  # professional, enthusiastic, casual
  max_length: 400  # words
```

### Phase 5: Tracking Integration

#### 5.1 Update Tracking to Include Cover Letters

**File**: `cli/integrations/tracking.py`

Add `cover_letter_generated` boolean field to tracking CSV.

### Phase 6: Testing

#### 6.1 Unit Tests

- `test_cover_letter_generator.py`: Test question determination, AI generation
- `test_job_detail_extraction.py`: Test parsing job descriptions

#### 6.2 Integration Tests

- Test full `generate-package` command with mock job description
- Test interactive mode with simulated user input
- Test non-interactive fallback behavior

## Implementation Order

1. **Week 1**: Core cover letter generator + template (Phase 1)
   - Create `cover_letter_generator.py`
   - Create `cover_letter_md.j2` template
   - Implement basic AI generation (no questions yet)

2. **Week 1-2**: Question/Answer system (Phase 2)
   - Implement `_determine_questions()` logic
   - Implement `_ask_question()` user prompts
   - Implement non-interactive fallback

3. **Week 2**: Package command (Phase 3)
   - Add `generate-package` command to CLI
   - Integrate resume + cover letter generation
   - Handle output directory structure

4. **Week 2**: Config and tracking (Phase 4-5)
   - Add cover letter config settings
   - Update tracking for cover letter generation

5. **Week 3**: Testing and refinement
   - Write tests
   - Test with real job descriptions
   - Refine AI prompts based on results

## File Changes Summary

### New Files
- `cli/generators/cover_letter_generator.py` - Main cover letter generator with PDF support
- `templates/cover_letter_md.j2` - Cover letter template
- `templates/cover_letter_tex.j2` - LaTeX template for PDF compilation (optional)
- `tests/test_cover_letter_generator.py` - Tests

### Modified Files
- `cli/main.py` - Add `generate-package` command with `--company` option
- `config/default.yaml` - Add cover letter settings (formats, smart_guesses)
- `cli/integrations/tracking.py` - Track cover letter generation
- `cli/generators/template.py` - Add PDF compilation method for cover letters
- `CLAUDE.md` - Update documentation with new command

## Design Decisions (Finalized)

1. **Cover letter formats**: Both Markdown and PDF will be generated ✅

2. **Non-interactive mode**: AI will make smart guesses (generic but relevant statements) ✅

3. **Template customization**: Users can provide custom templates (future enhancement, not v1.0 priority) ⏳

4. **Company name extraction**: `--company` option added as fallback when job description doesn't clearly state company name ✅

5. **Output organization**: Subdirectories per application (`output/{company}-{date}/`) ✅
