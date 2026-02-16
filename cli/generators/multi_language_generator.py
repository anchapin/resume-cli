"""Multi-language resume generation using AI translation."""

import json
import os
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


# Supported languages
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "code": "en"},
    "es": {"name": "Spanish", "native_name": "Español", "code": "es"},
    "fr": {"name": "French", "native_name": "Français", "code": "fr"},
    "de": {"name": "German", "native_name": "Deutsch", "code": "de"},
    "pt": {"name": "Portuguese", "native_name": "Português", "code": "pt"},
    "zh": {"name": "Chinese (Simplified)", "native_name": "中文", "code": "zh"},
    "ja": {"name": "Japanese", "native_name": "日本語", "code": "ja"},
    "ko": {"name": "Korean", "native_name": "한국어", "code": "ko"},
}

# Language code to locale mapping
LOCALE_FORMATS = {
    "en": {"date_format": "MM/DD/YYYY", "phone_format": "+1-xxx-xxx-xxxx"},
    "es": {"date_format": "DD/MM/YYYY", "phone_format": "+34 xxx xxx xxx"},
    "fr": {"date_format": "DD/MM/YYYY", "phone_format": "+33 x xx xx xx xx"},
    "de": {"date_format": "DD.MM.YYYY", "phone_format": "+49 xxx xxxxxx"},
    "pt": {"date_format": "DD/MM/YYYY", "phone_format": "+55 xx xxxxx xxxx"},
    "zh": {"date_format": "YYYY/MM/DD", "phone_format": "+86 xxx xxxx xxxx"},
    "ja": {"date_format": "YYYY/MM/DD", "phone_format": "+81 xxx xxxx xxxx"},
    "ko": {"date_format": "YYYY.MM.DD", "phone_format": "+82 xx xxxx xxxx"},
}


class MultiLanguageResumeGenerator:
    """Generate resumes in multiple languages using AI translation."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize multi-language resume generator.

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
        target_language: str,
        variant: str = "base",
        output_format: str = "md",
    ) -> str:
        """
        Generate a resume in the target language.

        Args:
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            variant: Resume variant to use
            output_format: Output format (md, txt, tex, pdf)

        Returns:
            Translated resume content
        """
        if target_language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {target_language}. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
            )

        console.print(f"[bold blue]Generating resume in {SUPPORTED_LANGUAGES[target_language]['name']}...[/bold blue]")

        # Generate English resume first
        english_content = self.template_generator.generate(
            variant=variant, output_format="md", output_path=None
        )

        # Get resume sections
        experience = self.yaml_handler.get_experience(variant)
        skills = self.yaml_handler.get_skills(variant)
        education = self.yaml_handler.get_education()
        contact = self.yaml_handler.get_contact()

        # Translate content using AI
        translated_content = self._translate_with_ai(
            content=english_content,
            target_language=target_language,
            experience=experience,
            skills=skills,
            education=education,
            contact=contact,
        )

        return translated_content

    def _translate_with_ai(
        self,
        content: str,
        target_language: str,
        experience: List[Dict[str, Any]],
        skills: Dict[str, List[str]],
        education: List[Dict[str, Any]],
        contact: Dict[str, Any],
    ) -> str:
        """Translate resume content using AI."""
        lang_info = SUPPORTED_LANGUAGES[target_language]
        locale_info = LOCALE_FORMATS.get(target_language, LOCALE_FORMATS["en"])

        prompt = f"""You are a professional resume translator. Translate the following resume from English to {lang_info['name']} ({lang_info['native_name']}).

IMPORTANT TRANSLATION RULES:
1. Translate ONLY the content, keep the same structure and formatting (Markdown headers, bullet points, etc.)
2. Use professional, formal language appropriate for a job resume
3. Adapt dates to {lang_info['name']} format: {locale_info['date_format']}
4. Adapt phone numbers to format: {locale_info['phone_format']}
5. Keep technical terms, programming languages, and company names in English unless there's a widely accepted translation
6. Preserve all numbers, percentages, and metrics exactly as they are
7. Maintain the same level of formality and tone as the original
8. Do NOT add any explanations or notes - translate ONLY the resume content

Resume to translate:

{content}

Now translate to {lang_info['name']}:"""

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            return response.strip()

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] AI translation failed: {str(e)}")
            console.print("[dim]Returning original English content[/dim]")
            return content

    def list_supported_languages(self) -> Dict[str, Dict[str, str]]:
        """List all supported languages."""
        return SUPPORTED_LANGUAGES.copy()

    def detect_language_from_job_description(self, job_description: str) -> Optional[str]:
        """
        Detect the target language from a job description.

        Args:
            job_description: Job description text

        Returns:
            Detected language code or None
        """
        # Simple language detection based on common words
        language_indicators = {
            "es": ["ingeniero", "desarrollador", "experiencia", "trabajo", "empresa"],
            "fr": ["ingénieur", "développeur", "expérience", "travail", "entreprise"],
            "de": ["ingenieur", "entwickler", "erfahrung", "arbeit", "unternehmen"],
            "pt": ["engenheiro", "desenvolvedor", "experiência", "trabalho", "empresa"],
            "zh": ["工程师", "开发", "经验", "工作", "公司"],
            "ja": ["エンジニア", "開発", "経験", "仕事", "会社"],
            "ko": ["엔지니어", "개발", "경력", "일", "회사"],
        }

        job_lower = job_description.lower()

        detected = None
        max_matches = 0

        for lang_code, indicators in language_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in job_lower)
            if matches > max_matches:
                max_matches = matches
                detected = lang_code

        if max_matches > 0:
            console.print(f"[dim]Detected language: {SUPPORTED_LANGUAGES[detected]['name']}[/dim]")
            return detected

        return None

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        model = self.config.ai_model

        message = self.client.messages.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 8000),
            temperature=self.config.get("ai.temperature", 0.3),  # Lower temp for translation
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        model = self.config.ai_model

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 8000),
            temperature=self.config.get("ai.temperature", 0.3),
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


def generate_multi_language_resume(
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    target_language: str = "es",
    variant: str = "base",
    output_format: str = "md",
) -> str:
    """
    Convenience function to generate a multi-language resume.

    Args:
        yaml_path: Path to resume.yaml
        config: Configuration object
        target_language: Target language code
        variant: Resume variant to use
        output_format: Output format

    Returns:
        Translated resume content
    """
    generator = MultiLanguageResumeGenerator(yaml_path, config)
    return generator.generate(
        target_language=target_language,
        variant=variant,
        output_format=output_format,
    )
