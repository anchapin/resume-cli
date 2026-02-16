"""AI-powered cover letter generator using Claude or OpenAI."""

# Import hashlib before kubernetes_asyncio can patch it
# Use sha256 instead of md5 to avoid kubernetes_asyncio patching
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

_sha256 = hashlib.sha256

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

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..utils.config import Config
from ..utils.yaml_parser import ResumeYAML
from .ai_judge import create_ai_judge
from .template import TemplateGenerator


class CoverLetterGenerator:
    """Generate personalized cover letters with AI."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize cover letter generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.yaml_handler = ResumeYAML(yaml_path)
        self.template_generator = TemplateGenerator(yaml_path, config=config)

        # Set up template directory
        template_dir = Path(__file__).parent.parent.parent / "templates"

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add now() function for templates
        self.env.globals["now"] = datetime.now

        # Add LaTeX escape filter (reuse from template_generator)
        def latex_escape(text):
            """Escape special LaTeX characters."""
            if not text:
                return text
            replacements = {
                "&": r"\&",
                "%": r"\%",
                "$": r"\$",
                "#": r"\#",
                "_": r"\_",
                "{": r"\{",
                "}": r"\}",
                "~": r"\textasciitilde{}",
                "^": r"\^{}",
                "™": r"\textsuperscript{TM}",
                "®": r"\textsuperscript{R}",
                "©": r"\textcopyright{}",
                "°": r"\textsuperscript{\textdegree}{}",
                "±": r"$\pm$",
                "≥": r"$\ge$",
                "≤": r"$\le$",
                "→": r"$\rightarrow$",
                "—": r"---",  # em dash
                "–": r"--",  # en dash
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text

        self.env.filters["latex_escape"] = latex_escape

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

    def generate_interactive(
        self,
        job_description: str,
        company_name: Optional[str] = None,
        variant: str = "base",
        output_formats: List[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Generate cover letter interactively, asking questions as needed.

        Args:
            job_description: Job description text
            company_name: Optional company name override
            variant: Variant name for resume context
            output_formats: List of output formats (md, pdf)
            output_dir: Optional output directory

        Returns:
            (dict of format -> content, job_details dict including question_answers)
        """
        # Extract job details
        job_details = self._extract_job_details(job_description, company_name)

        # Determine what questions to ask
        questions = self._determine_questions(job_details)

        # Ask questions
        question_answers = {}
        if questions:
            console.print("\n[bold cyan]Cover Letter Customization[/bold cyan]")
            console.print(f"Company: {job_details.get('company', 'Unknown')}")
            console.print(f"Position: {job_details.get('position', 'Unknown')}\n")

        for q in questions:
            answer = self._ask_question(q["question"], q.get("required", False))
            if answer:  # Store non-empty answers
                question_answers[q["key"]] = answer

        # Add question answers to job_details
        job_details["question_answers"] = question_answers

        # Generate cover letter content
        cover_letter_content = self._generate_with_ai(job_description, job_details, variant)

        # Render template
        rendered = self._render_template(cover_letter_content, job_details)

        # Generate outputs
        if output_formats is None:
            output_formats = self.config.get("cover_letter.formats", ["md"])

        results = {}
        for fmt in output_formats:
            if fmt == "md":
                results["md"] = rendered
            elif fmt == "pdf":
                # Generate LaTeX first, then compile to PDF
                latex_content = self._render_latex(cover_letter_content, job_details)
                results["pdf"] = latex_content  # This is LaTeX content that will be compiled

        return results, job_details

    def generate_non_interactive(
        self,
        job_description: str,
        company_name: Optional[str] = None,
        variant: str = "base",
        output_formats: List[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Generate cover letter non-interactively using AI smart guesses.

        Args:
            job_description: Job description text
            company_name: Optional company name override
            variant: Variant name for resume context
            output_formats: List of output formats (md, pdf)
            output_dir: Optional output directory

        Returns:
            (dict of format -> content, job_details dict)
        """
        # Extract job details
        job_details = self._extract_job_details(job_description, company_name)

        # Generate smart guesses for questions
        question_answers = self._generate_smart_guesses(job_description, job_details, variant)

        # Add question answers to job_details
        job_details["question_answers"] = question_answers

        # Generate cover letter content
        cover_letter_content = self._generate_with_ai(job_description, job_details, variant)

        # Render template
        rendered = self._render_template(cover_letter_content, job_details)

        # Generate outputs
        if output_formats is None:
            output_formats = self.config.get("cover_letter.formats", ["md"])

        results = {}
        for fmt in output_formats:
            if fmt == "md":
                results["md"] = rendered
            elif fmt == "pdf":
                # Generate LaTeX first, then compile to PDF
                latex_content = self._render_latex(cover_letter_content, job_details)
                results["pdf"] = latex_content  # This is LaTeX content that will be compiled

        return results, job_details

    def _extract_job_details(
        self, job_description: str, company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract key details from job description using AI.

        Args:
            job_description: Job description text
            company_name: Optional company name override

        Returns:
            Dict with company, position, requirements, etc.
        """
        # If company name provided, use it
        if company_name:
            company = company_name
        else:
            # Try to extract company name using AI
            company = self._extract_company_with_ai(job_description)

        # Extract other details with AI
        prompt = f"""Extract the following information from this job posting. Return ONLY a JSON object with these exact keys:
- company: the company name
- position: the job title
- requirements: list of key requirements/skills (3-5 items)
- company_mission: any mention of company mission, values, or culture (or null if not mentioned)

Job posting:
{job_description}

Return ONLY valid JSON, nothing else."""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse JSON from response
            import json

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                details = json.loads(json_match.group(0))
            else:
                details = {}

            # Override company if provided
            if company_name:
                details["company"] = company_name

            return {
                "company": details.get("company") or company,
                "position": details.get("position", "the open position"),
                "requirements": details.get("requirements", []),
                "company_mission": details.get("company_mission"),
            }

        except Exception as e:
            # Fallback to basic extraction
            return {
                "company": company or "the company",
                "position": "the open position",
                "requirements": [],
                "company_mission": None,
            }

    def _extract_company_with_ai(self, job_description: str) -> str:
        """Extract company name from job description using AI."""
        prompt = f"""Extract the company name from this job posting. Return ONLY the company name, nothing else. If no company name is mentioned, return "Unknown Company".

Job posting:
{job_description}"""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            company = response.strip().strip('"').strip("'")
            if company and company.lower() != "unknown company":
                return company
        except Exception:
            pass

        return "the company"

    def _determine_questions(self, job_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decide what questions to ask based on job details.

        Args:
            job_details: Extracted job information

        Returns:
            List of question dicts with 'key', 'question', 'required' keys
        """
        questions = []

        company = job_details.get("company", "the company")
        position = job_details.get("position", "this role")

        # Always ask about motivation
        questions.append(
            {
                "key": "motivation",
                "question": f"What specifically excites you about the {position} role at {company}?",
                "required": True,
            }
        )

        # Check for company-specific context
        if job_details.get("company_mission"):
            questions.append(
                {
                    "key": "company_alignment",
                    "question": f"What aspects of {company}'s mission or values resonate with you? (Press Enter to skip)",
                    "required": False,
                }
            )

        # Ask about connections
        questions.append(
            {
                "key": "connection",
                "question": f"Do you have any connections at {company} or have you spoken with anyone there? (Press Enter to skip)",
                "required": False,
            }
        )

        return questions

    def _ask_question(self, question: str, required: bool = False) -> str:
        """
        Prompt user for input.

        Args:
            question: Question to ask
            required: Whether an answer is required

        Returns:
            User's answer
        """
        while True:
            try:
                # Use Rich to print the prompt with color
                console.print(f"[yellow]?[/yellow] {question}", end=" ")
                answer = input().strip()
                if answer or not required:
                    return answer
                console.print("[red]This field is required. Please provide an answer.[/red]")
            except EOFError:
                if not required:
                    return ""
                raise

    def _generate_smart_guesses(
        self, job_description: str, job_details: Dict[str, Any], variant: str
    ) -> Dict[str, str]:
        """
        Generate AI-based smart guesses for cover letter questions.

        Args:
            job_description: Original job description
            job_details: Extracted job details
            variant: Resume variant for context

        Returns:
            Dict of question_key -> guessed_answer
        """
        # Get resume context
        contact = self.yaml_handler.get_contact()
        summary = self.yaml_handler.get_summary(variant)
        skills = self.yaml_handler.get_skills(variant)
        experience = self.yaml_handler.get_experience(variant)

        # Build resume summary for AI
        resume_summary = f"""
Name: {contact.get('name', '')}
Summary: {summary}

Skills: {list(skills.keys())}

Recent roles:
"""
        for job in experience[:3]:
            resume_summary += f"- {job.get('title', '')} at {job.get('company', '')}\n"

        prompt = f"""You are helping write a cover letter. Based on the job description and resume below, generate appropriate responses for a cover letter. Be truthful and positive.

**Resume:**
{resume_summary}

**Job Description:**
{job_description}

**Company:** {job_details.get('company', 'the company')}

Generate a JSON object with these keys:
- motivation: 1-2 sentences explaining why this role is a good fit based on the alignment between the job requirements and the candidate's experience
- company_alignment: {f"1 sentence about what aspects of {job_details.get('company')}''s mission resonate" if job_details.get('company_mission') else "null"}
- connection: null (assume no connection unless explicitly stated)

Return ONLY valid JSON, nothing else."""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            import json

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                guesses = json.loads(json_match.group(0))
                return guesses

        except Exception as e:
            pass

        # Fallback to generic responses
        return {
            "motivation": f"I am excited about this opportunity at {job_details.get('company', 'your company')} because it aligns well with my experience and skills.",
            "company_alignment": None,
            "connection": None,
        }

    def _generate_with_ai(
        self, job_description: str, job_details: Dict[str, Any], variant: str
    ) -> Dict[str, Any]:
        """
        Generate cover letter sections using AI with multi-generation and judge.

        Generates 3 versions, uses AI judge to select/combine the best.
        Results are cached to avoid regenerating for same inputs.

        Args:
            job_description: Original job description
            job_details: Job details + question answers
            variant: Resume variant

        Returns:
            Dict with cover letter sections
        """
        # Create cache key from inputs
        qa = job_details.get("question_answers", {})
        cache_key_input = f"{job_description[:500]}{str(qa)}{variant}"
        # usedforsecurity=False was added in Python 3.9, removed for 3.8 compatibility
        cache_key = _sha256(cache_key_input.encode()).hexdigest()

        # Check cache
        if cache_key in self._content_cache:
            return self._content_cache[cache_key]

        # Get resume context
        contact = self.yaml_handler.get_contact()
        summary = self.yaml_handler.get_summary(variant)
        skills = self.yaml_handler.get_skills(variant)
        experience = self.yaml_handler.get_experience(variant)

        # Build resume context
        resume_context = f"""
**Summary:** {summary}

**Skills:** {skills}

**Experience:**
"""
        for job in experience[:3]:
            bullets_text = "\n".join(
                [
                    f"  - {b.get('text', '') if isinstance(b, dict) else b}"
                    for b in job.get("bullets", [])[:2]
                ]
            )
            resume_context += f"- {job.get('title')} at {job.get('company')}\n{bullets_text}\n"

        # Get question answers
        qa = job_details.get("question_answers", {})

        # Build prompt (same for all generations)
        prompt = self._build_cover_letter_prompt(job_description, job_details, resume_context, qa)

        # Generate multiple versions
        versions = []
        num_generations = self.num_generations if self.judge_enabled else 1

        for i in range(num_generations):
            try:
                version = self._generate_single_version(prompt)
                if version:
                    versions.append(version)
            except Exception as e:
                # Log error but continue trying other generations
                console.print(f"[yellow]Warning:[/yellow] Generation {i+1} failed: {str(e)}")
                continue

        # If no successful generations, use fallback
        if not versions:
            result = self._get_fallback_content(job_details, summary)
            self._content_cache[cache_key] = result
            return result

        # If only one successful generation, return it
        if len(versions) == 1:
            result = versions[0]
            self._content_cache[cache_key] = result
            return result

        # Use judge to select best version (or combine)
        if self.judge_enabled:
            try:
                selected, justification = self.judge.judge_cover_letter(
                    versions, job_description, job_details, resume_context
                )
                console.print(f"[dim]AI Judge: {justification}[/dim]")
                self._content_cache[cache_key] = selected
                return selected
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Judge evaluation failed: {str(e)}. Using first version."
                )
                result = versions[0]
                self._content_cache[cache_key] = result
                return result

        # Fallback to first version
        result = versions[0]
        self._content_cache[cache_key] = result
        return result

    def _build_cover_letter_prompt(
        self,
        job_description: str,
        job_details: Dict[str, Any],
        resume_context: str,
        qa: Dict[str, Any],
    ) -> str:
        """Build the cover letter generation prompt."""
        return f"""You are an expert cover letter writer. Generate a professional cover letter based on the information below.

**Job Description:**
{job_description}

**Company:** {job_details.get('company')}
**Position:** {job_details.get('position')}

**Candidate Resume:**
{resume_context}

**Candidate's Motivation:** {qa.get('motivation', '')}

**Instructions:**
1. Write a compelling cover letter that is truthful and professional
2. Focus on the candidate's relevant experience and skills
3. Tailor the content to the job requirements
4. Keep it concise and professional
5. Do NOT add any fake experience or skills

Return ONLY a JSON object with these keys:
- opening_hook: A complete opening paragraph that includes the position name, company name, and expresses interest (e.g., "I am writing to express my strong interest in the [Position] role at [Company], as I am eager to apply my [relevant experience]...")
- professional_summary: 2-3 sentences highlighting relevant experience
- key_achievements: list of 3-4 specific achievements from the resume that match the job
- skills_highlight: list of 2-3 skill areas that are most relevant
- company_alignment: {f"1-2 sentences about {qa.get('company_alignment', 'company alignment')}" if qa.get('company_alignment') else "null"}
- connection: {f"a sentence about the connection: {qa.get('connection')}" if qa.get('connection') and qa.get('connection').lower() not in ['no', 'none', 'n/a'] else "null"}

Return ONLY valid JSON, nothing else."""

    def _generate_single_version(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Generate a single cover letter version.

        Args:
            prompt: The generation prompt

        Returns:
            Dict with cover letter sections, or None if failed
        """
        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            import json

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception:
            pass
        return None

    def _get_fallback_content(self, job_details: Dict[str, Any], summary: str) -> Dict[str, Any]:
        """Get fallback cover letter content when AI generation fails."""
        company = job_details.get("company", "your company")
        position = job_details.get("position", "this position")
        return {
            "opening_hook": f"I am writing to express my strong interest in the {position} role at {company}.",
            "professional_summary": summary[:200] if summary else "",
            "key_achievements": [
                "Proven track record of delivering high-quality software solutions",
                "Experience working with modern technologies and best practices",
                "Strong collaborative skills and team-oriented approach",
            ],
            "skills_highlight": ["Software Development", "Problem Solving", "Team Collaboration"],
            "company_alignment": None,
            "connection": None,
        }

    def _render_template(self, content: Dict[str, Any], job_details: Dict[str, Any]) -> str:
        """Render Markdown cover letter template."""
        contact = self.yaml_handler.get_contact()

        template = self.env.get_template("cover_letter_md.j2")

        context = {
            "contact": contact,
            "company_name": job_details.get("company"),
            "position_name": job_details.get("position"),
            "hiring_manager_name": None,  # Could be added as a question later
            "company_address": None,
            "opening_hook": content.get("opening_hook", ""),
            "professional_summary": content.get("professional_summary", ""),
            "key_achievements": content.get("key_achievements", []),
            "skills_highlight": content.get("skills_highlight", []),
            "company_alignment": content.get("company_alignment"),
            "connection": content.get("connection"),
        }

        return template.render(**context)

    def _render_latex(self, content: Dict[str, Any], job_details: Dict[str, Any]) -> str:
        """Render LaTeX cover letter template."""
        contact = self.yaml_handler.get_contact()

        template = self.env.get_template("cover_letter_tex.j2")

        context = {
            "contact": contact,
            "company_name": job_details.get("company"),
            "position_name": job_details.get("position"),
            "hiring_manager_name": None,
            "company_address": None,
            "opening_hook": content.get("opening_hook", ""),
            "professional_summary": content.get("professional_summary", ""),
            "key_achievements": content.get("key_achievements", []),
            "skills_highlight": content.get("skills_highlight", []),
            "company_alignment": content.get("company_alignment"),
            "connection": content.get("connection"),
        }

        return template.render(**context)

    def save_outputs(
        self, outputs: Dict[str, str], company_name: str, output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Save cover letter outputs to files.

        Args:
            outputs: Dict of format -> content
            company_name: Company name for filename (not used if output_dir is a full path)
            output_dir: Optional output directory (can be the package directory)

        Returns:
            Dict of format -> saved file path
        """
        if output_dir is None:
            # Create package directory in default output location
            output_base_dir = Path(self.config.output_dir)
            date_str = datetime.now().strftime("%Y-%m-%d")
            company_slug = re.sub(r"[^\w\s-]", "", company_name).strip().lower()[:30]
            company_slug = re.sub(r"[-\s]+", "-", company_slug)
            output_dir = output_base_dir / f"{company_slug}-{date_str}"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = {}

        # Save Markdown
        if "md" in outputs:
            md_path = output_dir / "cover-letter.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(outputs["md"])
            saved_paths["md"] = md_path

        # Save PDF
        if "pdf" in outputs:
            pdf_path = output_dir / "cover-letter.pdf"
            if self._compile_pdf(pdf_path, outputs["pdf"]):
                saved_paths["pdf"] = pdf_path
            else:
                # PDF compilation failed, but we have MD
                console.print(
                    "[yellow]Note:[/yellow] PDF compilation failed (pdflatex/pandoc not available). Cover letter saved as Markdown only."
                )

        return saved_paths

    def _compile_pdf(self, output_path: Path, tex_content: str) -> bool:
        """
        Compile LaTeX to PDF (reuse from TemplateGenerator).

        Args:
            output_path: Output PDF path
            tex_content: LaTeX content
        """
        # Create temporary .tex file
        tex_path = output_path.with_suffix(".tex")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Try pdflatex first
        import subprocess

        pdf_created = False
        try:
            # Use Popen with explicit cleanup to avoid double-free issues
            process = subprocess.Popen(
                ["pdflatex", "-interaction=nonstopmode", tex_path.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tex_path.parent,
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0 or output_path.exists():
                pdf_created = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Check if PDF was created anyway
            if output_path.exists():
                pdf_created = True
            else:
                # Fallback to pandoc
                try:
                    process = subprocess.Popen(
                        ["pandoc", str(tex_path), "-o", str(output_path), "--pdf-engine=xelatex"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    stdout, stderr = process.communicate()
                    if process.returncode == 0 or output_path.exists():
                        pdf_created = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

        if not pdf_created or not output_path.exists():
            # Return False to indicate PDF compilation failed
            return False

        return True

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


def generate_cover_letter(
    job_description: str,
    company_name: Optional[str] = None,
    variant: str = "base",
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    interactive: bool = True,
    **kwargs,
) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """
    Convenience function to generate cover letter.

    Args:
        job_description: Job description text
        company_name: Optional company name override
        variant: Resume variant name
        yaml_path: Path to resume.yaml
        config: Configuration object
        interactive: Whether to ask questions interactively
        **kwargs: Additional arguments

    Returns:
        (dict of format -> content, job_details dict)
    """
    generator = CoverLetterGenerator(yaml_path, config=config)

    if interactive:
        return generator.generate_interactive(
            job_description=job_description, company_name=company_name, variant=variant, **kwargs
        )
    else:
        return generator.generate_non_interactive(
            job_description=job_description, company_name=company_name, variant=variant, **kwargs
        )
