"""AI-powered resume generator using Claude or OpenAI."""

# Import hashlib before kubernetes_asyncio can patch it
# Use sha256 instead of md5 to avoid kubernetes_asyncio patching
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

_sha256 = hashlib.sha256

if sys.version_info >= (3, 9):
    _SHA256_KWARGS = {"usedforsecurity": False}
else:
    _SHA256_KWARGS = {}

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

from ..utils.config import Config
from .ai_judge import create_ai_judge
from .template import TemplateGenerator

# Initialize console for output
console = Console()


class AIGenerator:
    """Generate resumes using AI for customization."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
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
                    "anthropic package not installed. " "Install with: pip install 'resume-cli[ai]'"
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
                    "openai package not installed. " "Install with: pip install 'resume-cli[ai]'"
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

    def enhance_project_descriptions(
        self, projects: List[Dict[str, Any]], job_description: str, technologies: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate job-tailored project descriptions with technology highlights.

        This method enhances GitHub projects with AI-generated contextual descriptions
        that highlight relevant technologies and achievements. Enhancements are ephemeral
        (in-memory only) and do not modify the base resume.yaml.

        Args:
            projects: List of project dicts from GitHub (with name, description, url, language)
            job_description: Job description text
            technologies: List of relevant technologies extracted from job description

        Returns:
            Enhanced project list with added fields:
            - enhanced_description: 2-3 sentences emphasizing relevant tech
            - highlighted_technologies: List of tech names to highlight
            - achievement_highlights: List of specific achievements
            - relevance_score: Float 0-10 indicating job relevance
            Returns original projects on error (graceful degradation).
        """
        if not projects or not job_description:
            return projects

        # Check if enhancement is disabled in config
        if not self.config.get("github.enhance_descriptions", True):
            console.print("[dim]Project description enhancement disabled in config.[/dim]")
            return projects

        console.print("[dim]Enhancing project descriptions with AI...[/dim]")

        # Build prompt for batch enhancement
        projects_json = self._projects_to_json(projects)

        prompt = f"""You are an expert resume writer. I need you to enhance project descriptions to highlight relevant experience for a job application.

**Job Description:**
{job_description}

**Key Technologies to Highlight:**
{', '.join(technologies[:10]) if technologies else 'Various technologies'}

**Projects to Enhance:**
{projects_json}

**Instructions:**
1. For EACH project, generate an enhanced description (2-3 sentences) that emphasizes relevant technologies and achievements
2. Extract 3-5 highlighted technologies that match the job requirements (prioritize from the job description list)
3. Extract 2-4 achievement highlights as concise bullet points (start with action verbs: "Built", "Implemented", "Developed", etc.)
4. Assign a relevance score (0-10) based on how well the project matches the job requirements
5. **CRITICAL:** Do NOT invent features or achievements not implied by the project description/language
6. Focus on technologies and use cases that match the job description
7. Keep descriptions concise and professional

**Output Format:**
Return ONLY valid JSON as a list of objects with this exact structure:
[
  {{
    "name": "exact project name from input",
    "enhanced_description": "2-3 professional sentences emphasizing relevant tech...",
    "highlighted_technologies": ["Tech1", "Tech2", "Tech3"],
    "achievement_highlights": ["Built X using Y", "Implemented Z..."],
    "relevance_score": 8.5
  }}
]

**Requirements:**
- Return ONLY the JSON array, no introductory text
- Use exact project names from input
- All fields required for each project
- highlighted_technologies should prioritize job reqs, but can include other relevant tech
- achievement_highlights must be truthful based on project description/language
- relevance_score: 0-10 float (10 = perfect match, 5+ = good match)

Please generate the enhanced project descriptions:"""

        try:
            # Call AI API
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse JSON response
            import json

            extracted = self._extract_json(response)
            if not extracted:
                raise ValueError("No valid JSON found in AI response")
            enhanced_data = json.loads(extracted)

            if not isinstance(enhanced_data, list):
                raise ValueError("Response is not a list")

            # Merge enhanced data with original projects
            enhanced_projects = []
            enhancement_map = {ep["name"]: ep for ep in enhanced_data}

            for project in projects:
                project_copy = project.copy()
                project_name = project.get("name", "")

                if project_name in enhancement_map:
                    enhancement = enhancement_map[project_name]
                    project_copy.update(
                        {
                            "enhanced_description": enhancement.get("enhanced_description", ""),
                            "highlighted_technologies": enhancement.get(
                                "highlighted_technologies", []
                            ),
                            "achievement_highlights": enhancement.get("achievement_highlights", []),
                            "relevance_score": enhancement.get("relevance_score", 0.0),
                        }
                    )

                enhanced_projects.append(project_copy)

            console.print(
                f"[green]✓[/green] Enhanced {len(enhanced_projects)} project descriptions"
            )
            return enhanced_projects

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Project enhancement failed: {str(e)}")
            console.print("[dim]Using original project descriptions.[/dim]")
            return projects

    def generate_project_summary(
        self, enhanced_projects: List[Dict[str, Any]], base_summary: str, variant: str
    ) -> str:
        """
        Seamlessly integrate relevant projects into professional summary.

        This method generates an enhanced professional summary that incorporates
        2-3 most relevant projects while maintaining the original tone and structure.

        Args:
            enhanced_projects: List of enhanced project dicts (with relevance scores)
            base_summary: Original professional summary text
            variant: Variant name for context

        Returns:
            Enhanced summary text with integrated project mentions
            Returns base_summary on error (graceful degradation).
        """
        if not enhanced_projects or not base_summary:
            return base_summary

        # Check if summary enhancement is disabled in config
        if not self.config.get("github.enhance_summary", True):
            return base_summary

        console.print("[dim]Integrating projects into professional summary...[/dim]")

        # Sort by relevance and take top 3
        top_projects = sorted(
            enhanced_projects, key=lambda p: p.get("relevance_score", 0), reverse=True
        )[:3]

        projects_summary = "\n".join(
            [
                f"- {p.get('name', 'Project')}: {p.get('enhanced_description', p.get('description', ''))}"
                for p in top_projects
            ]
        )

        prompt = f"""You are an expert resume writer. I need you to seamlessly integrate relevant project experience into a professional summary.

**Original Professional Summary:**
{base_summary}

**Relevant Projects to Integrate:**
{projects_summary}

**Instructions:**
1. Keep the FIRST sentence of the original summary unchanged (it sets the tone)
2. Seamlessly integrate 2-3 of the most relevant projects into the narrative
3. Maintain the original summary's voice, style, and structure
4. Keep total length within ±20% of original summary
5. Focus on projects that demonstrate skills relevant to the job
6. Do NOT invent new experience or achievements
7. Make it flow naturally - project mentions should feel organic, not forced

**Output Format:**
- Return ONLY the enhanced summary text
- No introductory or concluding remarks
- Start directly with the first sentence (same as original)

Please generate the enhanced professional summary:"""

        try:
            # Call AI API
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            enhanced_summary = self._extract_from_code_block(response).strip()

            if enhanced_summary and len(enhanced_summary) > 50:
                console.print(
                    "[green]✓[/green] Professional summary enhanced with project experience"
                )
                return enhanced_summary
            else:
                return base_summary

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Summary enhancement failed: {str(e)}")
            console.print("[dim]Using original professional summary.[/dim]")
            return base_summary

    def _projects_to_json(self, projects: List[Dict[str, Any]]) -> str:
        """Convert projects list to JSON string for AI prompt."""
        import json

        # Extract only relevant fields for the prompt
        simplified = []
        for p in projects:
            simplified.append(
                {
                    "name": p.get("name", ""),
                    "description": p.get("description", ""),
                    "language": p.get("language", ""),
                    "url": p.get("url", ""),
                    "stars": p.get("stars", 0),
                }
            )
        return json.dumps(simplified, indent=2)

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
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
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
        fallback: bool = True,
        enhanced_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate AI-customized resume.

        Args:
            variant: Base variant to use
            job_description: Job description to tailor for
            output_format: Output format (md, tex, pdf)
            output_path: Optional output file path
            fallback: Whether to fallback to template on AI failure
            enhanced_context: Optional dict with AI-enhanced data (e.g., from GitHub projects)

        Returns:
            Generated resume content
        """
        try:
            # Generate base resume from template with enhanced_context if provided
            base_resume = self.template_generator.generate(
                variant=variant,
                output_format=output_format,
                output_path=None,
                enhanced_context=enhanced_context,
            )

            if job_description:
                # Customize with AI
                customized_resume = self._customize_with_ai(
                    base_resume=base_resume,
                    job_description=job_description,
                    variant=variant,
                    output_format=output_format,
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
                    output_path=output_path,
                    enhanced_context=enhanced_context,
                )
            else:
                raise

    def _customize_with_ai(
        self, base_resume: str, job_description: str, variant: str, output_format: str = "md"
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
        cache_key = _sha256(
            f"{job_description[:1000]}{variant}{output_format}".encode(),
            **_SHA256_KWARGS,
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

    def _extract_keywords(self, job_description: str) -> list:
        """Extract key skills and requirements from job description."""
        # Simple extraction - could be enhanced with NLP
        keywords = []

        # Common tech keywords
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "node.js",
            "django",
            "flask",
            "fastapi",
            "kubernetes",
            "docker",
            "aws",
            "gcp",
            "azure",
            "sql",
            "mongodb",
            "postgresql",
            "redis",
            "ci/cd",
            "devops",
            "machine learning",
            "ai",
            "llm",
            "pytorch",
            "tensorflow",
            "react native",
            "graphql",
            "rest api",
            "microservices",
        ]

        job_lower = job_description.lower()
        for keyword in tech_keywords:
            if keyword in job_lower:
                keywords.append(keyword)

        return keywords

    def _build_prompt(self, base_resume: str, job_description: str, keywords: list) -> str:
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
            r"```latex\s*\n(.*?)\n```",  # ```latex...```
            r"```\s*\n(.*?)\n```",  # ```...``` (any language)
            r"```latex\s+(.*?)```",  # ```latex content``` (single line)
            r"```\s+(.*?)```",  # ```content``` (single line)
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted:
                    return extracted

        # If no code blocks found, look for common AI intro patterns and skip them
        intro_patterns = [
            r"^(Here is[^\n]+\n)*",  # "Here is the resume..."
            r"^(Below is[^\n]+\n)*",  # "Below is the resume..."
            r"^(The customized resume[^\n]+\n)*",  # "The customized resume..."
            r'^("|\')[^"\']*\1\s*\n*',  # Quoted intro text
        ]

        cleaned = response
        for pattern in intro_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip() if cleaned.strip() else response

    def _extract_json(self, response: str) -> str:
        """
        Extract JSON from AI response, handling multiple formats.

        Args:
            response: AI response that should contain JSON

        Returns:
            Extracted JSON string, or empty string if not found
        """
        import re

        if not response:
            return ""

        # First, try to extract from code blocks
        code_block_content = self._extract_from_code_block(response)
        if code_block_content and code_block_content != response:
            # If we successfully extracted from code blocks, validate it's JSON-like
            stripped = code_block_content.strip()
            if stripped.startswith("[") or stripped.startswith("{"):
                return stripped

        # If code block extraction didn't work or returned same response,
        # try to find JSON array/object directly
        # Look for content between [ and ] or { and } at the top level
        json_match = re.search(r"\[\s*\{.*\}\s*\]", response, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()

        # Look for JSON object
        obj_match = re.search(r"\{[^{}]*\{[^{}]*\}[^{}]*\}", response, re.DOTALL)
        if obj_match:
            return obj_match.group(0).strip()

        # Fallback: return the original response stripped
        stripped = response.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
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

    def tailor_data(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
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
            # 2. Try parsing the whole response as JSON directly (for plain JSON responses)
            # 3. Fall back to non-greedy regex match (for responses with extra text)
            fenced_json_match = re.search(r"```json\s*(\{.*\})\s*```", response, re.DOTALL)
            if fenced_json_match:
                return json.loads(fenced_json_match.group(1))

            # Try to parse the whole response as JSON directly
            # This handles plain JSON responses without markdown
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

            # Try to extract JSON from response (in case of markdown or other wrappers)
            # Non-greedy match for simple JSON extraction
            json_match = re.search(r"(\{.*?\})", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # If all attempts fail, raise exception to trigger fallback
            raise ValueError("Could not extract valid JSON from response")

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Data tailoring failed: {str(e)}")
            return resume_data


def generate_with_ai(
    variant: str,
    job_description: Optional[str] = None,
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    **kwargs,
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
    return generator.generate(variant=variant, job_description=job_description, **kwargs)
