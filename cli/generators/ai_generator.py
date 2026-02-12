"""AI-powered resume generator using Claude or OpenAI."""

import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from rich.console import Console

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional but recommended

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
from ..utils.config import Config
from .ai_judge import create_ai_judge

# Initialize console for output
console = Console()


class AIGenerator:
    """Generate resumes using AI for customization."""

    def __init__(
        self,
        yaml_path: Optional[Path] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize AI generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.template_generator = TemplateGenerator(yaml_path, config=config)

        # Initialize AI client
        provider = self.config.ai_provider

        if provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install 'resume-cli[ai]'"
                )
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it with: export ANTHROPIC_API_KEY=your_key"
                )
            # Check env var first, then config file
            base_url = os.getenv("ANTHROPIC_BASE_URL") or self.config.anthropic_base_url
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = anthropic.Anthropic(**client_kwargs)
            self.provider = "anthropic"

        elif provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'resume-cli[ai]'"
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable not set. "
                    "Set it with: export OPENAI_API_KEY=your_key"
                )
            # Check env var first, then config file
            base_url = os.getenv("OPENAI_BASE_URL") or self.config.openai_base_url
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

    def extract_technologies(self, job_description: str) -> List[str]:
        """
        Extract technologies from job description using AI.

        Args:
            job_description: Job description text

        Returns:
            List of technology keywords (e.g., ["python", "react", "kubernetes"])
            Returns empty list on error
        """
        prompt = f"""Extract the key technologies, programming languages, frameworks, and tools mentioned in this job posting.

**Job Posting:**
{job_description}

**Instructions:**
- Extract ONLY specific technologies, languages, frameworks, and tools
- Include programming languages (e.g., Python, JavaScript, Go)
- Include frameworks and libraries (e.g., React, Django, TensorFlow)
- Include platforms and tools (e.g., Kubernetes, Docker, AWS)
- Use lowercase for all technologies
- Return ONLY a JSON array of strings

Return ONLY valid JSON, nothing else."""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse JSON from response
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                import json
                technologies = json.loads(json_match.group(0))
                if isinstance(technologies, list):
                    return [str(tech).lower().strip() for tech in technologies if tech]

            # Fallback: return empty list
            return []

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Technology extraction failed: {str(e)}")
            return []

    def generate(
        self,
        variant: str,
        job_description: Optional[str] = None,
        output_format: str = "md",
        output_path: Optional[Path] = None,
        fallback: bool = True
    ) -> str:
        """
        Generate AI-customized resume.

        Args:
            variant: Base variant to use
            job_description: Job description to tailor for
            output_format: Output format (md, tex, pdf)
            output_path: Optional output file path
            fallback: Whether to fallback to template on AI failure

        Returns:
            Generated resume content
        """
        try:
            # Generate base resume from template
            base_resume = self.template_generator.generate(
                variant=variant,
                output_format=output_format,
                output_path=None
            )

            if job_description:
                # Customize with AI
                customized_resume = self._customize_with_ai(
                    base_resume=base_resume,
                    job_description=job_description,
                    variant=variant,
                    output_format=output_format
                )
            else:
                customized_resume = base_resume

            # Save if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # If PDF requested, compile from TEX
                if output_format == "pdf" or output_path.suffix == ".pdf":
                    self.template_generator._compile_pdf(output_path, customized_resume)
                else:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(customized_resume)

            return customized_resume

        except Exception as e:
            if fallback and self.config.fallback_to_template:
                console.print(f"[yellow]AI generation failed: {e}[/yellow]")
                console.print("[yellow]Falling back to template generation...[/yellow]")

                return self.template_generator.generate(
                    variant=variant,
                    output_format=output_format,
                    output_path=output_path
                )
            else:
                raise

    def _customize_with_ai(
        self,
        base_resume: str,
        job_description: str,
        variant: str,
        output_format: str = "md"
    ) -> str:
        """
        Use AI to customize resume for job description with multi-generation and judge.

        Generates 3 versions, uses AI judge to select the best.
        Results are cached to avoid regenerating for same inputs.

        Args:
            base_resume: Base resume content
            job_description: Job description text
            variant: Variant name used
            output_format: Output format (md, tex, pdf) - included in cache key

        Returns:
            Customized resume content
        """
        # Create cache key from inputs (include output_format since content differs)
        import hashlib
        cache_key = hashlib.md5(
            f"{job_description[:1000]}{variant}{output_format}".encode()
        ).hexdigest()

        # Check cache - return customized content converted to requested format
        if cache_key in self._content_cache:
            cached = self._content_cache[cache_key]
            # The cached content might be in a different format (MD vs PDF)
            # But since customization is the same, we can use it directly
            # The caller will handle any format-specific conversions
            return cached

        # Extract key information from job description
        keywords = self._extract_keywords(job_description)

        # Build prompt (same for all generations)
        prompt = self._build_prompt(base_resume, job_description, keywords)

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
                    # Extract content from markdown code blocks if present
                    cleaned_response = self._extract_from_code_block(response)
                    versions.append(cleaned_response)
            except Exception as e:
                # Log error but continue trying other generations
                console.print(f"[yellow]Warning:[/yellow] Resume generation {i+1} failed: {str(e)}")
                continue

        # If no successful generations, return base resume
        if not versions:
            console.print("[yellow]Warning:[/yellow] All AI generations failed. Using base resume.")
            return base_resume

        # If only one successful generation, return it
        if len(versions) == 1:
            result = versions[0]
            self._content_cache[cache_key] = result
            return result

        # Use judge to select best version
        if self.judge_enabled:
            try:
                selected, justification = self.judge.judge_resume_text(
                    versions, job_description, base_resume
                )
                console.print(f"[dim]AI Judge (Resume): {justification}[/dim]")
                self._content_cache[cache_key] = selected
                return selected
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Judge evaluation failed: {str(e)}. Using first version.")
                result = versions[0]
                self._content_cache[cache_key] = result
                return result

        # Fallback to first version
        result = versions[0]
        self._content_cache[cache_key] = result
        return result

    def _extract_keywords(self, job_description: str) -> list:
        """Extract key skills and requirements from job description."""
        # Simple extraction - could be enhanced with NLP
        keywords = []

        # Common tech keywords
        tech_keywords = [
            "python", "javascript", "typescript", "react", "vue", "angular",
            "node.js", "django", "flask", "fastapi", "kubernetes", "docker",
            "aws", "gcp", "azure", "sql", "mongodb", "postgresql", "redis",
            "ci/cd", "devops", "machine learning", "ai", "llm", "pytorch",
            "tensorflow", "react native", "graphql", "rest api", "microservices"
        ]

        job_lower = job_description.lower()
        for keyword in tech_keywords:
            if keyword in job_lower:
                keywords.append(keyword)

        return keywords

    def _build_prompt(
        self,
        base_resume: str,
        job_description: str,
        keywords: list
    ) -> str:
        """Build AI prompt for resume customization."""
        prompt = f"""You are an expert resume writer. I need you to tailor my resume for a specific job description.

**Base Resume:**
{base_resume}

**Job Description:**
{job_description}

**Key Requirements Identified:**
{', '.join(keywords) if keywords else 'None specific'}

**Instructions:**
1. Keep the same overall structure and format
2. Emphasize experience and skills that match the job requirements
3. Reorder bullet points within each job to highlight relevant experience first
4. Do NOT add any fake experience, skills, or achievements
5. Do NOT change dates, company names, or job titles
6. If the job description emphasizes certain areas, you may expand slightly on relevant bullets (but keep truthful)
7. Keep the resume to a similar length as the original

**CRITICAL OUTPUT REQUIREMENTS:**
- Return ONLY the resume content itself
- NO introductory text, explanations, or commentary
- NO markdown code blocks (no ```latex or ``` wrappers)
- Start your response immediately with the first character of the resume content
- End your response immediately with the last character of the resume content

Please return the customized resume in the same format as the base resume:"""

        return prompt

    def _extract_from_code_block(self, response: str) -> str:
        """
        Extract content from markdown code blocks if present.

        Args:
            response: AI response that may contain markdown code blocks

        Returns:
            Extracted content without markdown wrappers, or original response
        """
        import re

        # Try to extract content from ```latex...``` or ```...``` blocks
        patterns = [
            r'```latex\s*\n(.*?)\n```',  # ```latex...```
            r'```\s*\n(.*?)\n```',       # ```...``` (any language)
            r'```latex\s+(.*?)```',      # ```latex content``` (single line)
            r'```\s+(.*?)```',           # ```content``` (single line)
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted:
                    return extracted

        # If no code blocks found, look for common AI intro patterns and skip them
        intro_patterns = [
            r'^(Here is[^\n]+\n)*',                    # "Here is the resume..."
            r'^(Below is[^\n]+\n)*',                   # "Below is the resume..."
            r'^(The customized resume[^\n]+\n)*',      # "The customized resume..."
            r'^("|\')[^"\']*\1\s*\n*',                 # Quoted intro text
        ]

        cleaned = response
        for pattern in intro_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip() if cleaned.strip() else response

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        model = self.config.ai_model

        message = self.client.messages.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 4000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        model = self.config.ai_model

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 4000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    def tailor_data(
        self,
        resume_data: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:
        """
        Tailor resume data (dict) to job description.

        Args:
            resume_data: Dictionary containing resume data
            job_description: Job description text

        Returns:
            Modified resume data dictionary
        """
        prompt = f"""You are an expert resume writer. I need you to tailor my resume data for a specific job description.

**Job Description:**
{job_description}

**Resume Data (JSON):**
{json.dumps(resume_data, indent=2)}

**Instructions:**
1. Analyze the job description and the resume data.
2. Modify the "professional_summary" to be more relevant to the job.
3. Reorder or select the most relevant "bullets" in the "experience" section.
4. Ensure the JSON structure remains EXACTLY the same.
5. Do NOT add fake experience.
6. Return ONLY the valid JSON of the modified resume data.

Return ONLY valid JSON, nothing else."""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse JSON from response
            # 1. Prefer JSON inside ```json ... ``` fences
            fenced_json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if fenced_json_match:
                return json.loads(fenced_json_match.group(1))

            # 2. Search for first '{' and try raw_decode (handles nested JSON correctly)
            start_idx = response.find('{')
            if start_idx != -1:
                try:
                    obj, _ = json.JSONDecoder().raw_decode(response[start_idx:])
                    return obj
                except json.JSONDecodeError:
                    pass

            # 3. Fallback: try to load the whole response as JSON
            return json.loads(response)

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Data tailoring failed: {str(e)}")
            # Re-raise exception so API can handle it properly instead of silently failing
            raise RuntimeError(f"Failed to parse AI response: {str(e)}")


def generate_with_ai(
    variant: str,
    job_description: Optional[str] = None,
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    **kwargs
) -> str:
    """
    Convenience function to generate resume with AI.

    Args:
        variant: Base variant name
        job_description: Job description text
        yaml_path: Path to resume.yaml
        config: Configuration object
        **kwargs: Additional arguments for generate()

    Returns:
        Generated resume content
    """
    generator = AIGenerator(yaml_path, config)
    return generator.generate(
        variant=variant,
        job_description=job_description,
        **kwargs
    )
