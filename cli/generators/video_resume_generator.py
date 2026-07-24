"""AI-powered video resume script generator using Claude or OpenAI."""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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

from ..utils.config import Config
from ..utils.yaml_parser import ResumeYAML
from .template import TemplateGenerator


class VideoResumeScript:
    """Represents a generated video resume script."""

    def __init__(self, duration_seconds: int):
        self.duration_seconds = duration_seconds
        self.introduction = ""
        self.key_achievements = []
        self.skills_highlight = ""
        self.call_to_action = ""
        self.visual_suggestions = []
        self.teleprompter_text = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_seconds": self.duration_seconds,
            "introduction": self.introduction,
            "key_achievements": self.key_achievements,
            "skills_highlight": self.skills_highlight,
            "call_to_action": self.call_to_action,
            "visual_suggestions": self.visual_suggestions,
            "teleprompter_text": self.teleprompter_text,
        }


class VideoResumeGenerator:
    """Generate personalized video resume scripts based on job description and resume."""

    # Duration presets
    DURATION_SHORT = 60  # 60 seconds
    DURATION_MEDIUM = 120  # 2 minutes
    DURATION_LONG = 300  # 5 minutes

    # Timing breakdowns (in seconds)
    TIMING_SHORT = {
        "introduction": 10,
        "achievements": 20,
        "skills": 20,
        "call_to_action": 10,
    }

    TIMING_MEDIUM = {
        "introduction": 20,
        "achievements": 40,
        "skills": 40,
        "call_to_action": 20,
    }

    TIMING_LONG = {
        "introduction": 30,
        "achievements": 90,
        "skills": 90,
        "call_to_action": 30,
    }

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize video resume generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.yaml_handler = ResumeYAML(yaml_path)
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

    def generate(
        self,
        job_description: str = "",
        variant: str = "base",
        duration: int = 60,
        company_name: str = "",
    ) -> VideoResumeScript:
        """
        Generate a video resume script.

        Args:
            job_description: Optional job description for targeting
            variant: Resume variant to use
            duration: Video duration in seconds (60, 120, or 300)
            company_name: Target company name

        Returns:
            VideoResumeScript object with all sections
        """
        # Normalize duration
        if duration <= 60:
            duration = self.DURATION_SHORT
        elif duration <= 150:
            duration = self.DURATION_MEDIUM
        else:
            duration = self.DURATION_LONG

        console.print(f"[bold blue]Generating {duration}-second video resume script...[/bold blue]")

        # Get resume data
        resume_content = self.template_generator.generate(
            variant=variant, output_format="md", output_path=None
        )

        experience = self.yaml_handler.get_experience(variant)
        skills = self.yaml_handler.get_skills(variant)
        contact = self.yaml_handler.get_contact()
        summary = self.yaml_handler.get_summary(variant)

        # Generate script using AI
        script = self._generate_script_with_ai(
            job_description=job_description,
            resume_content=resume_content,
            experience=experience,
            skills=skills,
            contact=contact,
            summary=summary,
            duration=duration,
            company_name=company_name,
        )

        return script

    def _generate_script_with_ai(
        self,
        job_description: str,
        resume_content: str,
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        contact: Dict[str, Any],
        summary: str,
        duration: int,
        company_name: str,
    ) -> VideoResumeScript:
        """Generate script using AI API."""
        # Build prompt
        prompt = self._build_script_prompt(
            job_description=job_description,
            resume_content=resume_content,
            experience=experience,
            skills=skills,
            contact=contact,
            summary=summary,
            duration=duration,
            company_name=company_name,
        )

        try:
            # Call AI API
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse response
            script = self._parse_script_response(response, duration)

            return script

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] AI generation failed: {str(e)}")
            console.print("[dim]Falling back to template-based script...[/dim]")
            return self._generate_fallback_script(
                contact=contact,
                experience=experience,
                skills=skills,
                duration=duration,
                company_name=company_name,
            )

    def _build_script_prompt(
        self,
        job_description: str,
        resume_content: str,
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        contact: Dict[str, Any],
        summary: str,
        duration: int,
        company_name: str,
    ) -> str:
        """Build AI prompt for script generation."""
        # Format experience
        experience_text = ""
        for exp in experience[:3]:  # Top 3 jobs
            company = exp.get("company", "Unknown")
            title = exp.get("title", "Unknown Role")
            bullets = exp.get("bullets", [])[:3]  # Top 3 bullets
            bullet_text = "\n".join([f"  - {b.get('text', '')}" for b in bullets if b.get("text")])
            experience_text += f"\n{title} at {company}\n{bullet_text}\n"

        # Format skills
        skills_text = ""
        all_skills = []
        for category, skill_list in skills.items():
            if skill_list:
                if isinstance(skill_list[0], dict):
                    skill_names = [s.get("name", s) for s in skill_list]
                else:
                    skill_names = skill_list
                all_skills.extend(skill_names)
                skills_text += f"\n{category}: {', '.join(str(s) for s in skill_names[:5])}"

        # top_skills removed - was unused

        # Timing breakdown
        if duration <= 60:
            timing = self.TIMING_SHORT
        elif duration <= 150:
            timing = self.TIMING_MEDIUM
        else:
            timing = self.TIMING_LONG

        company_context = f"Targeting {company_name}" if company_name else "General job application"

        prompt = f"""You are an expert career coach and video script writer. Generate a compelling video resume script based on the candidate's resume and job description.

**Target Duration:** {duration} seconds
- Introduction: {timing['introduction']} seconds
- Key Achievements: {timing['achievements']} seconds
- Skills Highlight: {timing['skills']} seconds
- Call to Action: {timing['call_to_action']} seconds

**Job Description:**
{job_description if job_description else "Not provided - create a general video script"}

**Candidate's Professional Summary:**
{summary[:500] if summary else "Not provided"}

**Candidate's Work Experience:**
{experience_text}

**Candidate's Skills:**
{skills_text}

**Candidate's Contact:**
Name: {contact.get('name', 'Your Name')}
Email: {contact.get('email', 'your@email.com')}
{github_link if (github_link := contact.get('github')) else ''}
{linkedin_link if (linkedin_link := contact.get('linkedin')) else ''}

**Context:** {company_context}

**Instructions:**
Generate a video resume script that is:
1. Confident and professional but not boastful
2. Specific with real numbers and achievements
3. Targeted to the job description (if provided)
4. Natural to speak (conversational, not scripted-sounding)

**For each section, provide:**
1. The spoken script (what to say)
2. Visual suggestions (what to show on screen)
3. Teleprompter-friendly formatting

**Output Format:**
Return ONLY valid JSON as a single object with this exact structure:
{{
  "introduction": {{
    "script": "What to say in the introduction",
    "visual": "What to show on screen",
    "teleprompter": "Teleprompter text",
    "start_time": 0,
    "end_time": {timing['introduction']}
  }},
  "key_achievements": [
    {{
      "achievement": "Specific achievement with metrics",
      "script": "How to phrase this achievement",
      "visual": "What to show (e.g., metrics graphic)",
      "teleprompter": "Teleprompter text"
    }}
  ],
  "skills_highlight": {{
    "script": "What to say about your skills",
    "skills_mentioned": ["skill1", "skill2"],
    "visual": "What to show (e.g., skill icons)",
    "teleprompter": "Teleprompter text"
  }},
  "call_to_action": {{
    "script": "Closing statement with contact info",
    "visual": "Contact info on screen",
    "teleprompter": "Teleprompter text"
  }},
  "visual_suggestions": ["suggestion1", "suggestion2"],
  "total_duration": {duration}
}}

**Requirements:**
- Return ONLY the JSON object, no introductory text
- Use real metrics from the resume (percentages, dollar amounts, numbers)
- Match the tone to the job (technical for engineering, leadership for management)
- Keep script natural and conversational
- Include specific achievements with numbers where possible

Please generate the video resume script JSON:"""

        return prompt

    def _parse_script_response(self, response: str, duration: int) -> VideoResumeScript:
        """Parse AI response into VideoResumeScript object."""
        # Extract JSON from response
        json_str = self._extract_json(response)
        if not json_str:
            raise ValueError("Could not parse AI response as JSON")

        data = json.loads(json_str)

        # Create script object
        script = VideoResumeScript(duration)

        # Parse introduction
        if "introduction" in data:
            intro = data["introduction"]
            script.introduction = intro.get("script", "")
            script.visual_suggestions.append(f"Intro: {intro.get('visual', '')}")
            script.teleprompter_text += f"[Introduction]\n{intro.get('teleprompter', '')}\n\n"

        # Parse achievements
        if "key_achievements" in data:
            for ach in data["key_achievements"]:
                script.key_achievements.append(
                    {
                        "achievement": ach.get("achievement", ""),
                        "script": ach.get("script", ""),
                        "visual": ach.get("visual", ""),
                    }
                )
                script.teleprompter_text += f"[Achievement]\n{ach.get('teleprompter', '')}\n\n"

        # Parse skills
        if "skills_highlight" in data:
            skills = data["skills_highlight"]
            script.skills_highlight = skills.get("script", "")
            script.visual_suggestions.append(f"Skills: {skills.get('visual', '')}")
            script.teleprompter_text += f"[Skills]\n{skills.get('teleprompter', '')}\n\n"

        # Parse call to action
        if "call_to_action" in data:
            cta = data["call_to_action"]
            script.call_to_action = cta.get("script", "")
            script.visual_suggestions.append(f"CTA: {cta.get('visual', '')}")
            script.teleprompter_text += f"[Call to Action]\n{cta.get('teleprompter', '')}\n\n"

        # Additional visual suggestions
        if "visual_suggestions" in data:
            script.visual_suggestions.extend(data["visual_suggestions"])

        return script

    def _generate_fallback_script(
        self,
        contact: Dict[str, Any],
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        duration: int,
        company_name: str,
    ) -> VideoResumeScript:
        """Generate a basic script without AI."""
        script = VideoResumeScript(duration)

        name = contact.get("name", "there")
        email = contact.get("email", "myemail@example.com")
        github = contact.get("github", "")

        # Get top achievement from first job
        top_achievement = ""
        if experience and experience[0].get("bullets"):
            top_achievement = experience[0]["bullets"][0].get("text", "")

        # Get top skills
        all_skills = []
        for skill_list in skills.values():
            if skill_list:
                if isinstance(skill_list[0], dict):
                    all_skills.extend([s.get("name", s) for s in skill_list])
                else:
                    all_skills.extend(skill_list)
        top_skills = ", ".join(all_skills[:5]) if all_skills else "my technical skills"

        company_ref = f" at {company_name}" if company_name else ""

        # Introduction
        script.introduction = (
            f"Hi, I'm {name}. Thank you for considering my application{company_ref}."
        )

        # Achievements
        script.key_achievements = [
            {
                "achievement": top_achievement,
                "script": f"I've {top_achievement.lower() if top_achievement else 'contributed to significant projects'}.",
                "visual": "Show a relevant project or metric",
            }
        ]

        # Skills
        script.skills_highlight = f"My expertise includes {top_skills}."

        # Call to action
        contact_info = f"{email}"
        if github:
            contact_info += f" or check out my work at {github}"
        script.call_to_action = (
            f"I'd love to bring my experience to your team. Reach me at {contact_info}. Thank you!"
        )

        # Visual suggestions
        script.visual_suggestions = [
            "Intro: Headshot with name/title on screen",
            "Achievements: Show relevant metrics or project",
            "Skills: Display skill icons or logos",
            "CTA: Contact information on screen",
        ]

        # Teleprompter text
        script.teleprompter_text = f"""[Introduction]
{script.introduction}

[Achievement]
{script.key_achievements[0]['script'] if script.key_achievements else ''}

[Skills]
{script.skills_highlight}

[Call to Action]
{script.call_to_action}
"""

        return script

    def _extract_json(self, response: str) -> str:
        """Extract JSON from AI response."""
        if not response:
            return ""

        # Try to extract from code blocks
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Look for JSON object
        obj_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if obj_match:
            return obj_match.group(0).strip()

        # Fallback
        stripped = response.strip()
        if stripped.startswith("{"):
            return stripped

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

    def render_to_markdown(self, script: VideoResumeScript) -> str:
        """Render script to Markdown format."""
        lines = []

        # Header
        duration_display = f"{script.duration_seconds // 60}:{script.duration_seconds % 60:02d}"
        lines.append("# Video Resume Script")
        lines.append(f"\n**Duration:** {duration_display} ({script.duration_seconds} seconds)")
        lines.append("")

        # Introduction
        lines.append("## Introduction")
        lines.append("")
        lines.append(f"**Time:** 0:00 - 0:{min(10, script.duration_seconds // 6):02d}")
        lines.append("")
        lines.append(f"**Script:** {script.introduction}")
        lines.append("")

        # Achievements
        if script.key_achievements:
            lines.append("## Key Achievements")
            lines.append("")
            ach_duration = script.duration_seconds // 3
            for i, ach in enumerate(script.key_achievements):
                start_time = 10 + i * (ach_duration // max(len(script.key_achievements), 1))
                lines.append(f"### Achievement {i + 1}")
                lines.append(
                    f"**Time:** 0:{start_time:02d} - 0:{start_time + ach_duration // len(script.key_achievements):02d}"
                )
                lines.append("")
                lines.append(f"**Achievement:** {ach.get('achievement', '')}")
                lines.append(f"**Script:** {ach.get('script', '')}")
                lines.append(f"**Visual:** {ach.get('visual', '')}")
                lines.append("")

        # Skills
        if script.skills_highlight:
            lines.append("## Skills Highlight")
            lines.append("")
            lines.append(f"**Script:** {script.skills_highlight}")
            lines.append("")

        # Call to Action
        if script.call_to_action:
            lines.append("## Call to Action")
            lines.append("")
            lines.append(f"**Script:** {script.call_to_action}")
            lines.append("")

        # Visual Suggestions
        if script.visual_suggestions:
            lines.append("## Visual Suggestions")
            lines.append("")
            for suggestion in script.visual_suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")

        # Teleprompter Text
        if script.teleprompter_text:
            lines.append("## Teleprompter Text")
            lines.append("")
            lines.append("```")
            lines.append(script.teleprompter_text.strip())
            lines.append("```")
            lines.append("")

        # Filming Checklist
        lines.append("## Filming Checklist")
        lines.append("")
        lines.append("- [ ] Choose good lighting (natural or soft box)")
        lines.append("- [ ] Position camera at eye level")
        lines.append("- [ ] Test audio (no background noise)")
        lines.append("- [ ] Wear solid color clothing")
        lines.append("- [ ] Have teleprompter or notes ready")
        lines.append("- [ ] Practice script 3-5 times before recording")
        lines.append("- [ ] Record multiple takes, keep the best one")
        lines.append("- [ ] Edit to remove any mistakes or long pauses")
        lines.append("")

        return "\n".join(lines)

    def render_to_teleprompter(self, script: VideoResumeScript) -> str:
        """Render script in teleprompter-friendly format."""
        lines = []

        # Calculate timing
        if script.duration_seconds <= 60:
            timing = self.TIMING_SHORT
        elif script.duration_seconds <= 150:
            timing = self.TIMING_MEDIUM
        else:
            timing = self.TIMING_LONG

        # Header
        lines.append("=" * 50)
        lines.append(f"VIDEO RESUME - {script.duration_seconds} seconds")
        lines.append("=" * 50)
        lines.append("")

        # Introduction with timing
        lines.append(f"[0:00 - 0:{timing['introduction']:02d}] INTRODUCTION")
        lines.append("-" * 30)
        lines.append(script.introduction)
        lines.append("")

        # Achievements with timing
        if script.key_achievements:
            ach_per_section = timing["achievements"] // max(len(script.key_achievements), 1)
            current_time = timing["introduction"]
            for i, ach in enumerate(script.key_achievements):
                lines.append(
                    f"[0:{current_time:02d} - 0:{current_time + ach_per_section:02d}] ACHIEVEMENT {i + 1}"
                )
                lines.append("-" * 30)
                lines.append(ach.get("script", ""))
                lines.append("")
                current_time += ach_per_section

        # Skills with timing
        if script.skills_highlight:
            lines.append(f"[0:{current_time:02d} - 0:{current_time + timing['skills']:02d}] SKILLS")
            lines.append("-" * 30)
            lines.append(script.skills_highlight)
            lines.append("")
            current_time += timing["skills"]

        # Call to Action with timing
        if script.call_to_action:
            lines.append(f"[0:{current_time:02d} - 0:{script.duration_seconds:02d}] CALL TO ACTION")
            lines.append("-" * 30)
            lines.append(script.call_to_action)
            lines.append("")

        return "\n".join(lines)


def generate_video_resume(
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    job_description: str = "",
    variant: str = "base",
    duration: int = 60,
    company_name: str = "",
) -> VideoResumeScript:
    """
    Convenience function to generate a video resume script.

    Args:
        yaml_path: Path to resume.yaml
        config: Configuration object
        job_description: Optional job description
        variant: Resume variant to use
        duration: Video duration in seconds
        company_name: Target company name

    Returns:
        VideoResumeScript object
    """
    generator = VideoResumeGenerator(yaml_path, config)
    return generator.generate(
        job_description=job_description,
        variant=variant,
        duration=duration,
        company_name=company_name,
    )
