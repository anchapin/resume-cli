"""AI-powered interview questions generator using Claude or OpenAI."""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from rich.console import Console

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Initialize console for output
console = Console()

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .template import TemplateGenerator
from ..utils.yaml_parser import ResumeYAML
from ..utils.config import Config
from .ai_judge import create_ai_judge


class InterviewQuestionsGenerator:
    """Generate personalized interview questions based on job description and resume."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize interview questions generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.yaml_handler = ResumeYAML(yaml_path)
        self.template_generator = TemplateGenerator(yaml_path, config=config)

        # Initialize AI client (same as AIGenerator)
        provider = self.config.ai_provider

        if provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "anthropic package not installed. " "Install with: pip install 'resume-cli[ai]'"
                )
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it with: export ANTHROPIC_API_KEY=your_key"
                )
            base_url = os.getenv("ANTHROPIC_BASE_URL") or self.config.get(
                "ai.anthropic_base_url", ""
            )
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = anthropic.Anthropic(**client_kwargs)
            self.provider = "anthropic"

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai package not installed. " "Install with: pip install 'resume-cli[ai]'"
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Set it with: export OPENAI_API_KEY=your_key"
                )
            base_url = os.getenv("OPENAI_BASE_URL") or self.config.get("ai.openai_base_url", "")
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = openai.OpenAI(**client_kwargs)
            self.provider = "openai"
        else:
            raise ValueError(f"Unknown AI provider: {provider}")

        # Initialize AI Judge
        self.judge = create_ai_judge(self.client, self.provider, self.config)
        self.num_generations = self.config.get("ai.num_generations", 3)
        self.judge_enabled = self.config.get("ai.judge_enabled", True)

        # Cache to avoid regenerating content for same inputs
        self._content_cache = {}

    def clear_cache(self):
        """Clear the content cache. Useful when generating for different jobs."""
        self._content_cache.clear()

    def generate(
        self,
        job_description: str,
        variant: str = "base",
        num_technical: int = 10,
        num_behavioral: int = 5,
        include_system_design: bool = True,
        flashcard_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate interview questions based on job description.

        Args:
            job_description: Job description text
            variant: Variant name for resume context
            num_technical: Number of technical questions to generate
            num_behavioral: Number of behavioral questions to generate
            include_system_design: Whether to include system design questions
            flashcard_mode: If True, output is optimized for flashcard format (question on front, answer on back)

        Returns:
            Dict containing:
            - technical_questions: List of technical question dicts
            - behavioral_questions: List of behavioral question dicts
            - system_design_questions: List of system design question dicts (if included)
            - job_analysis: Analysis of job requirements
        """
        console.print("[bold blue]Generating interview questions...[/bold blue]")

        # Generate resume content for context
        resume_content = self.template_generator.generate(
            variant=variant, output_format="md", output_path=None
        )

        # Extract resume experience and skills
        experience = self.yaml_handler.get_experience(variant)
        skills = self.yaml_handler.get_skills(variant)

        # Generate questions using AI with multi-generation and judge
        questions_data = self._generate_questions_with_ai(
            job_description=job_description,
            resume_content=resume_content,
            experience=experience,
            skills=skills,
            num_technical=num_technical,
            num_behavioral=num_behavioral,
            include_system_design=include_system_design,
            flashcard_mode=flashcard_mode,
        )

        return questions_data

    def _generate_questions_with_ai(
        self,
        job_description: str,
        resume_content: str,
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        num_technical: int,
        num_behavioral: int,
        include_system_design: bool,
        flashcard_mode: bool,
    ) -> Dict[str, Any]:
        """
        Generate questions using AI with multi-generation and judge selection.

        Args:
            job_description: Job description text
            resume_content: Full resume as markdown
            experience: List of experience entries from resume
            skills: Dict of skill categories
            num_technical: Number of technical questions
            num_behavioral: Number of behavioral questions
            include_system_design: Whether to include system design questions
            flashcard_mode: Whether to optimize for flashcard format

        Returns:
            Dict with generated questions and job analysis
        """
        # Build prompt for question generation
        prompt = self._build_questions_prompt(
            job_description=job_description,
            resume_content=resume_content,
            experience=experience,
            skills=skills,
            num_technical=num_technical,
            num_behavioral=num_behavioral,
            include_system_design=include_system_design,
            flashcard_mode=flashcard_mode,
        )

        # Generate multiple versions
        versions = []
        num_generations = self.num_generations if self.judge_enabled else 1

        for i in range(num_generations):
            try:
                # Call AI API
                if self.provider == "anthropic":
                    response = self._call_anthropic(prompt)
                else:
                    response = self._call_openai(prompt)

                if response:
                    # Extract JSON from response
                    extracted_json = self._extract_json(response)
                    if extracted_json:
                        versions.append(json.loads(extracted_json))
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Question generation {i+1} failed: {str(e)}"
                )
                continue

        # If no successful generations, return empty structure
        if not versions:
            console.print("[yellow]Warning:[/yellow] All AI generations failed.")
            return {
                "technical_questions": [],
                "behavioral_questions": [],
                "system_design_questions": [] if include_system_design else None,
                "job_analysis": {},
            }

        # If only one successful generation, return it
        if len(versions) == 1:
            result = versions[0]
            return result

        # Use judge to select best version
        if self.judge_enabled:
            try:
                selected = self.judge.judge_interview_questions(
                    versions, job_description, resume_content
                )
                console.print(f"[dim]AI Judge (Interview Questions): Selected best version[/dim]")
                return selected
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Judge evaluation failed: {str(e)}. Using first version."
                )
                return versions[0]

        # Fallback to first version
        return versions[0]

    def _build_questions_prompt(
        self,
        job_description: str,
        resume_content: str,
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        num_technical: int,
        num_behavioral: int,
        include_system_design: bool,
        flashcard_mode: bool,
    ) -> str:
        """Build AI prompt for interview question generation."""
        # Format experience for prompt
        experience_text = ""
        for exp in experience:
            company = exp.get("company", "Unknown Company")
            title = exp.get("title", "Unknown Role")
            bullets = exp.get("bullets", [])
            bullet_text = "\n".join([f"  - {b.get('text', '')}" for b in bullets if b.get("text")])
            experience_text += f"\n{title} at {company}\n{bullet_text}\n"

        # Format skills for prompt
        skills_text = ""
        for category, skill_list in skills.items():
            if skill_list:
                if isinstance(skill_list[0], dict):
                    # Handle skill objects with emphasize_for
                    skill_names = [s.get("name", s) for s in skill_list]
                else:
                    skill_names = skill_list
                skills_text += f"\n{category}: {', '.join(str(s) for s in skill_names[:10])}"

        mode_instruction = (
            (
                "Provide concise, self-contained answers suitable for flashcards (front: question, back: answer). "
                "Keep answers to 2-3 sentences maximum."
            )
            if flashcard_mode
            else ("Provide detailed, comprehensive answers with multiple talking points.")
        )

        system_design_section = (
            """
**System Design Questions:**
Generate {num_system} system design questions relevant to the role and technologies.

For each system design question:
- question: The design question
- context: Why this question is relevant (based on job requirements or candidate's experience)
- key_areas: List of areas to discuss (e.g., scalability, consistency, availability)
- reference: Specific resume experience relevant to this design challenge
- talking_points: 4-6 key points to cover in the answer
- complexity: Difficulty level (easy, medium, hard)
""".format(
                num_system=3 if include_system_design else 0
            )
            if include_system_design
            else ""
        )

        prompt = f"""You are an expert technical interviewer and career coach. Generate relevant interview questions based on a job description and candidate's resume.

**Job Description:**
{job_description}

**Candidate's Resume (Summary):**
{resume_content[:2000]}

**Candidate's Work Experience:**
{experience_text}

**Candidate's Skills:**
{skills_text}

**Instructions:**

1. **Analyze the Job:** Identify the key technical requirements, technologies, and skills mentioned in the job description.

2. **Generate Technical Questions ({num_technical} questions):**
   For each technical question, provide:
   - question: Clear, specific technical question
   - priority: high, medium, or low (based on importance to job requirements)
   - category: Question category (e.g., "Python", "System Design", "Databases", "APIs")
   - context: Why this question is being asked (reference specific job requirements)
   - reference: Specific resume bullets or experience relevant to this question
   - answer: {mode_instruction}
   - tips: 2-3 key points to emphasize when answering

3. **Generate Behavioral Questions ({num_behavioral} questions):**
   For each behavioral question, provide:
   - question: Situational/behavioral question
   - priority: high, medium, or low
   - framework: Interview framework to use (e.g., "STAR Method", "PARLA")
   - context: Why this question is being asked (e.g., leadership, teamwork, problem-solving)
   - reference: Specific resume experience that relates to this behavioral area
   - answer: {mode_instruction}
   - tips: How to structure a compelling answer using the framework

{system_design_section}

4. **Job Analysis:**
   - key_technologies: List of top 5-10 technologies/skills from the job description
   - role_type: Type of role (e.g., "Backend Engineer", "Fullstack Developer", "ML Engineer")
   - focus_areas: List of main focus areas (e.g., "API Design", "Performance Optimization", "Machine Learning")
   - difficulty_estimate: Overall difficulty of interview (entry, mid, senior)

**Output Format:**
Return ONLY valid JSON as a single object with this exact structure:
{{
  "technical_questions": [
    {{
      "question": "Question text",
      "priority": "high|medium|low",
      "category": "Category name",
      "context": "Why this question matters",
      "reference": "Specific resume experience",
      "answer": "Answer/talking points",
      "tips": ["Tip 1", "Tip 2"]
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "Question text",
      "priority": "high|medium|low",
      "framework": "STAR Method",
      "context": "Why this question matters",
      "reference": "Specific resume experience",
      "answer": "Answer/talking points",
      "tips": ["Tip 1", "Tip 2"]
    }}
  ],
  "system_design_questions": [  // Omit if include_system_design is false
    {{
      "question": "Design question",
      "context": "Why this question matters",
      "key_areas": ["scalability", "consistency"],
      "reference": "Specific resume experience",
      "talking_points": ["Point 1", "Point 2"],
      "complexity": "medium"
    }}
  ],
  "job_analysis": {{
    "key_technologies": ["Tech1", "Tech2"],
    "role_type": "Backend Engineer",
    "focus_areas": ["Area 1", "Area 2"],
    "difficulty_estimate": "senior"
  }}
}}

**Requirements:**
- Return ONLY the JSON object, no introductory text
- Ensure all questions reference the candidate's actual resume experience
- Match questions to the job description requirements
- Vary priority levels (mix of high, medium, low)
- For technical questions, include specific technical details from the job description
- For behavioral questions, focus on soft skills relevant to the role (leadership, communication, teamwork)
- All answer content should be truthful based on the resume provided
- {mode_instruction}

Please generate the interview questions JSON:"""

        return prompt

    def render_to_markdown(self, questions_data: Dict[str, Any]) -> str:
        """
        Render questions to Markdown format.

        Args:
            questions_data: Dict with questions from generate()

        Returns:
            Markdown string with formatted questions
        """
        lines = []

        # Job Analysis section
        job_analysis = questions_data.get("job_analysis", {})
        if job_analysis:
            lines.append("# Interview Preparation Guide")
            lines.append("")
            lines.append("## Job Analysis")
            lines.append("")
            lines.append(f"**Role Type:** {job_analysis.get('role_type', 'Unknown')}")
            lines.append(f"**Difficulty:** {job_analysis.get('difficulty_estimate', 'Unknown')}")
            lines.append("")
            lines.append("**Key Technologies:**")
            for tech in job_analysis.get("key_technologies", []):
                lines.append(f"- {tech}")
            lines.append("")
            lines.append("**Focus Areas:**")
            for area in job_analysis.get("focus_areas", []):
                lines.append(f"- {area}")
            lines.append("")

        # Technical Questions
        tech_questions = questions_data.get("technical_questions", [])
        if tech_questions:
            lines.append("## Technical Questions")
            lines.append("")

            # Group by priority
            high_priority = [q for q in tech_questions if q.get("priority") == "high"]
            medium_priority = [q for q in tech_questions if q.get("priority") == "medium"]
            low_priority = [q for q in tech_questions if q.get("priority") == "low"]

            if high_priority:
                lines.append("### High Priority")
                lines.append("")
                for q in high_priority:
                    lines.extend(self._format_question(q, include_answer=True))
                lines.append("")

            if medium_priority:
                lines.append("### Medium Priority")
                lines.append("")
                for q in medium_priority:
                    lines.extend(self._format_question(q, include_answer=True))
                lines.append("")

            if low_priority:
                lines.append("### Low Priority")
                lines.append("")
                for q in low_priority:
                    lines.extend(self._format_question(q, include_answer=True))
                lines.append("")

        # Behavioral Questions
        behavioral_questions = questions_data.get("behavioral_questions", [])
        if behavioral_questions:
            lines.append("## Behavioral Questions")
            lines.append("")

            for q in behavioral_questions:
                lines.extend(self._format_question(q, include_answer=True, is_behavioral=True))
                lines.append("")

        # System Design Questions
        system_design_questions = questions_data.get("system_design_questions")
        if system_design_questions:
            lines.append("## System Design Questions")
            lines.append("")

            for q in system_design_questions:
                lines.extend(self._format_system_design_question(q))
                lines.append("")

        return "\n".join(lines)

    def render_to_flashcards(self, questions_data: Dict[str, Any]) -> str:
        """
        Render questions to flashcard format (question only, optimized for studying).

        Args:
            questions_data: Dict with questions from generate()

        Returns:
            Markdown string with flashcard-formatted questions
        """
        lines = []
        lines.append("# Interview Flashcards")
        lines.append("")

        # Technical Questions
        tech_questions = questions_data.get("technical_questions", [])
        if tech_questions:
            lines.append("## Technical Questions")
            lines.append("")

            for i, q in enumerate(tech_questions, 1):
                lines.append(f"### Q{i}. {q['question']}")
                lines.append("")
                lines.append(f"*Priority: {q.get('priority', 'medium').upper()}*")
                lines.append(f"*Category: {q.get('category', 'General')}*")
                lines.append("")
                if q.get("answer"):
                    lines.append("**Answer / Talking Points:**")
                    lines.append(q["answer"])
                    lines.append("")
                if q.get("tips"):
                    lines.append("**Tips:**")
                    for tip in q["tips"]:
                        lines.append(f"- {tip}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # Behavioral Questions
        behavioral_questions = questions_data.get("behavioral_questions", [])
        if behavioral_questions:
            lines.append("## Behavioral Questions")
            lines.append("")

            for i, q in enumerate(behavioral_questions, 1):
                lines.append(f"### Q{i}. {q['question']}")
                lines.append("")
                lines.append(f"*Priority: {q.get('priority', 'medium').upper()}*")
                lines.append(f"*Framework: {q.get('framework', 'STAR Method')}*")
                lines.append("")
                if q.get("answer"):
                    lines.append("**Answer Framework:**")
                    lines.append(q["answer"])
                    lines.append("")
                if q.get("tips"):
                    lines.append("**Tips:**")
                    for tip in q["tips"]:
                        lines.append(f"- {tip}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        # System Design Questions
        system_design_questions = questions_data.get("system_design_questions")
        if system_design_questions:
            lines.append("## System Design Questions")
            lines.append("")

            for i, q in enumerate(system_design_questions, 1):
                lines.append(f"### Q{i}. {q['question']}")
                lines.append("")
                lines.append(f"*Complexity: {q.get('complexity', 'medium').upper()}*")
                lines.append("")
                lines.append("**Key Areas to Discuss:**")
                for area in q.get("key_areas", []):
                    lines.append(f"- {area}")
                lines.append("")
                if q.get("talking_points"):
                    lines.append("**Talking Points:**")
                    for point in q["talking_points"]:
                        lines.append(f"- {point}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    def _format_question(
        self, question: Dict[str, Any], include_answer: bool = True, is_behavioral: bool = False
    ) -> List[str]:
        """Format a single question for Markdown output."""
        lines = []

        lines.append(f"**{question['question']}**")
        lines.append("")

        if question.get("context"):
            lines.append(f"*Context: {question['context']}*")
            lines.append("")

        if question.get("category"):
            lines.append(f"*Category: {question['category']}*")
        if question.get("framework"):
            lines.append(f"*Framework: {question['framework']}*")
        if question.get("priority"):
            lines.append(f"*Priority: {question['priority'].upper()}*")
        lines.append("")

        if question.get("reference"):
            lines.append("**Relevant Experience:**")
            lines.append(question["reference"])
            lines.append("")

        if include_answer and question.get("answer"):
            lines.append("**Answer:**")
            lines.append(question["answer"])
            lines.append("")

        if question.get("tips"):
            lines.append("**Tips:**")
            for tip in question["tips"]:
                lines.append(f"- {tip}")
            lines.append("")

        return lines

    def _format_system_design_question(self, question: Dict[str, Any]) -> List[str]:
        """Format a system design question for Markdown output."""
        lines = []

        lines.append(f"**{question['question']}**")
        lines.append("")

        if question.get("context"):
            lines.append(f"*Context: {question['context']}*")
            lines.append("")

        if question.get("reference"):
            lines.append("**Relevant Experience:**")
            lines.append(question["reference"])
            lines.append("")

        lines.append("**Key Areas to Discuss:**")
        for area in question.get("key_areas", []):
            lines.append(f"- {area}")
        lines.append("")

        if question.get("talking_points"):
            lines.append("**Talking Points:**")
            for point in question["talking_points"]:
                lines.append(f"- {point}")
            lines.append("")

        return lines

    def _extract_json(self, response: str) -> str:
        """
        Extract JSON from AI response.

        Args:
            response: AI response that should contain JSON

        Returns:
            Extracted JSON string, or empty string if not found
        """
        if not response:
            return ""

        # Try to extract from code blocks
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Look for JSON object
        obj_match = re.search(r"\{[^{}]*\{[^{}]*\}[^{}]*\}", response, re.DOTALL)
        if obj_match:
            return obj_match.group(0).strip()

        # Fallback: return the original response stripped
        stripped = response.strip()
        if stripped.startswith("{"):
            return stripped

        # No valid JSON found
        return ""

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        model = self.config.ai_model

        message = self.client.messages.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 4000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        model = self.config.ai_model

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 4000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


import os  # Import os here for environment variable access
