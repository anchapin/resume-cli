# Interview Preparation Guide

The `resume-cli interview-prep` command generates personalized interview questions based on a job description and your resume, complete with answers and tips.

## Features

### Question Categories

- **Technical Questions**: Domain-specific questions matched to job requirements
- **Behavioral Questions**: Situational questions using STAR/PARLA frameworks
- **System Design Questions**: Architecture and scalability questions (for engineering roles)

### Question Generation

- Parses job description for key skills and technologies
- Generates questions that reference your actual resume experience
- Prioritizes questions by importance (high, medium, low)
- Provides context, answers, and talking points for each question

### Output Formats

- **Standard Mode**: Detailed format with context, answers, and tips
- **Flashcard Mode**: Concise format optimized for studying (question front, answer back)

## Usage

### Basic Usage

```bash
# Generate interview questions using default settings
resume-cli interview-prep --job-desc job-posting.txt

# Generate with more questions
resume-cli interview-prep --job-desc job.txt --num-technical 15 --num-behavioral 8

# Generate flashcard format for studying
resume-cli interview-prep --job-desc job.txt --flashcard-mode

# Specify output file
resume-cli interview-prep --job-desc job.txt -o interview-prep.md
```

### Full Example

```bash
# Generate comprehensive interview preparation
resume-cli interview-prep \
  --job-desc sample_job_description.txt \
  --variant v1.1.0-backend \
  --num-technical 12 \
  --num-behavioral 6 \
  -o interview-prep-techcorp.md
```

### Output Structure

Generated output includes:

1. **Job Analysis**
   - Role type (e.g., "Backend Engineer")
   - Difficulty estimate (entry, mid, senior)
   - Key technologies from job description
   - Focus areas for interview preparation

2. **Technical Questions** (by priority)
   - High Priority: Most critical skills for the role
   - Medium Priority: Important but less critical
   - Low Priority: Nice-to-have topics

3. **Behavioral Questions**
   - Questions about teamwork, leadership, problem-solving
   - STAR Method framework guidance
   - References to specific resume experiences

4. **System Design Questions** (optional)
   - Architecture challenges relevant to the role
   - Key areas to discuss (scalability, consistency, etc.)
   - Talking points based on your experience

## Question Format

Each question includes:

- **Question**: Clear, specific interview question
- **Priority**: Importance level (high/medium/low)
- **Category/Type**: Technical category or behavioral framework
- **Context**: Why this question is relevant
- **Reference**: Specific resume bullets or experience
- **Answer**: Suggested answer or talking points
- **Tips**: 2-3 key points to emphasize

## Examples

### Technical Question

```
**Describe your experience with microservices architecture.**

*Priority: HIGH*
*Category: System Architecture*

*Context: The job requires building scalable distributed systems.*

**Relevant Experience:**
- Designed and implemented microservices architecture using Django and FastAPI
- Built RESTful APIs serving 100K+ daily requests

**Answer:**
I have extensive experience with microservices from my work at Tech Corp. I designed and implemented a microservices architecture using Django and FastAPI, breaking down a monolithic application into independent services. Each service has a single responsibility and communicates via REST APIs. This approach improved team productivity and allowed for independent scaling. We implemented service discovery and API gateways to manage traffic routing.

**Tips:**
- Discuss the trade-offs you considered (when to use vs not use microservices)
- Mention specific challenges you faced (data consistency, testing, deployment)
- Talk about communication patterns (synchronous vs asynchronous)
```

### Behavioral Question (STAR Method)

```
**Tell me about a time you had to disagree with a colleague on a technical approach.**

*Priority: MEDIUM*
*Framework: STAR Method*

*Context: Assessing your conflict resolution and communication skills.*

**Relevant Experience:**
- Mentored 3 junior developers, conducting code reviews and pair programming sessions
- Collaborated with cross-functional teams on product features

**Answer:**
Use the STAR Method:
- **Situation**: During a code review, a junior developer implemented a solution using a complex pattern
- **Task**: I needed to provide feedback while maintaining a positive learning environment
- **Action**: I scheduled a 1-on-1 meeting to understand their approach, explained my concerns, and showed a simpler alternative with code examples
- **Result**: They implemented the simpler approach, which improved code maintainability, and we established a pattern for future similar discussions

**Tips:**
- Focus on resolution and professional approach
- Emphasize learning outcomes for both parties
- Avoid blaming or criticizing the colleague
- Show how you maintained the relationship
```

## Configuration

Interview preparation settings can be configured in `config/default.yaml`:

```yaml
interview_prep:
  enabled: true
  output_directory: output
  default_num_technical: 10
  default_num_behavioral: 5
  include_system_design: true
  flashcard_answer_max_length: 150  # characters for concise answers
  frameworks:
    - "STAR Method"
    - "PARLA"
    - "Situation-Action-Result"
```

## Tips for Effective Interview Prep

1. **Start Early**: Generate questions at least a week before the interview
2. **Practice Aloud**: Don't just read your answers - practice saying them
3. **Be Specific**: Reference actual projects and results from your resume
4. **Ask Questions**: Prepare thoughtful questions to ask the interviewer
5. **Review Regularly**: Review your notes multiple times before the interview

## Study Strategies

### Flashcard Mode

Use flashcard mode for quick review sessions:

```bash
resume-cli interview-prep --job-desc job.txt --flashcard-mode
```

This produces concise cards:
- Front: Question only
- Back: Answer + key tips

### Role-Specific Preparation

Use different variants to target different roles:

```bash
# Backend role
resume-cli interview-prep --job-desc backend-job.txt --variant v1.1.0-backend

# Fullstack role
resume-cli interview-prep --job-desc fullstack-job.txt --variant v1.3.0-fullstack
```

### Mock Interviews

Use the generated questions to conduct mock interviews:
- Ask a friend to read the questions to you
- Time your answers (2-3 minutes for behavioral, 5-10 for technical)
- Record yourself and review for improvements

## Troubleshooting

### "anthropic package not installed"

Install AI dependencies:
```bash
pip install -e ".[ai]"
```

### "ANTHROPIC_API_KEY not set"

Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Or create a `.env` file from `.env.template`.

### No questions generated

Check that:
- The job description has clear technical requirements
- Your resume has relevant experience
- The AI API key is valid
- You have internet connectivity

### Questions seem generic

This can happen if:
- Job description is vague or very brief
- Resume doesn't have matching experience
- AI model generated generic responses

Try:
- Providing a more detailed job description
- Using a variant with relevant experience
- Adjusting the `num_technical` and `num_behavioral` parameters
