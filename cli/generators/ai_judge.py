"""AI Judge agent for evaluating and selecting the best AI-generated content."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

# Initialize console for output
console = Console()


class AIJudge:
    """AI-powered judge for evaluating generated resumes and cover letters."""

    def __init__(self, client, provider: str, config):
        """
        Initialize AI Judge.

        Args:
            client: Anthropic or OpenAI client instance
            provider: 'anthropic' or 'openai'
            config: Config object
        """
        self.client = client
        self.provider = provider
        self.config = config

    def judge_cover_letter(
        self,
        versions: List[Dict[str, Any]],
        job_description: str,
        job_details: Dict[str, Any],
        resume_context: str,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Evaluate and select best cover letter version.

        Args:
            versions: List of 3 cover letter JSON outputs
            job_description: Original job description
            job_details: Extracted job details
            resume_context: Candidate's resume summary

        Returns:
            (selected_version, justification_text)
        """
        if len(versions) == 0:
            raise ValueError("No versions to judge")

        if len(versions) == 1:
            return versions[0], "Only one version available."

        # Create comparison prompt
        prompt = self._create_cover_letter_judge_prompt(
            versions, job_description, job_details, resume_context
        )

        try:
            # Call AI to judge
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(response)

            # Parse judge's decision
            decision = self._parse_judge_response(response)

            if decision.get("action") == "combine":
                # Judge wants to combine elements from multiple versions
                combined = self._combine_versions(versions, decision.get("selection", {}))
                return combined, decision.get(
                    "justification", "Combined best elements from multiple versions."
                )

            # Judge selected a specific version
            selected_idx = decision.get("selected", 0)
            if 0 <= selected_idx < len(versions):
                return versions[selected_idx], decision.get(
                    "justification", f"Selected version {selected_idx + 1}."
                )

        except Exception as e:
            # On judge failure, return first version with note
            return versions[0], f"Judge evaluation failed: {str(e)}. Using first version."

        # Fallback to first version
        return versions[0], "Judge unable to decide. Using first version."

    def judge_resume_customization(
        self, versions: List[Dict[str, Any]], job_description: str, resume_context: str
    ) -> Tuple[Dict[str, Any], str]:
        """
        Evaluate and select best resume customization (structured data).

        Args:
            versions: List of 3 resume customization outputs (structured)
            job_description: Original job description
            resume_context: Full resume context

        Returns:
            (selected_version, justification_text)
        """
        if len(versions) == 0:
            raise ValueError("No versions to judge")

        if len(versions) == 1:
            return versions[0], "Only one version available."

        # Create comparison prompt
        prompt = self._create_resume_judge_prompt(versions, job_description, resume_context)

        try:
            # Call AI to judge
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse judge's decision
            decision = self._parse_judge_response(response)

            if decision.get("action") == "combine":
                # Judge wants to combine elements
                combined = self._combine_versions(versions, decision.get("selection", {}))
                return combined, decision.get(
                    "justification", "Combined best elements from multiple versions."
                )

            # Judge selected a specific version
            selected_idx = decision.get("selected", 0)
            if 0 <= selected_idx < len(versions):
                return versions[selected_idx], decision.get(
                    "justification", f"Selected version {selected_idx + 1}."
                )

        except Exception as e:
            # On judge failure, return first version
            return versions[0], f"Judge evaluation failed: {str(e)}. Using first version."

        # Fallback to first version
        return versions[0], "Judge unable to decide. Using first version."

    def judge_resume_text(
        self, versions: List[str], job_description: str, base_resume: str
    ) -> Tuple[str, str]:
        """
        Evaluate and select best full resume text version.

        Args:
            versions: List of 3 full resume text outputs
            job_description: Original job description
            base_resume: Original base resume for comparison

        Returns:
            (selected_resume_text, justification_text)
        """
        if len(versions) == 0:
            raise ValueError("No versions to judge")

        if len(versions) == 1:
            return versions[0], "Only one version available."

        # Create comparison prompt for full resumes
        prompt = self._create_resume_text_judge_prompt(versions, job_description, base_resume)

        try:
            # Call AI to judge
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse judge's decision
            decision = self._parse_judge_response(response)

            # Judge selected a specific version
            selected_idx = decision.get("selected", 0)
            if 0 <= selected_idx < len(versions):
                return versions[selected_idx], decision.get(
                    "justification", f"Selected version {selected_idx + 1}."
                )

        except Exception as e:
            # On judge failure, return first version
            return versions[0], f"Judge evaluation failed: {str(e)}. Using first version."

        # Fallback to first version
        return versions[0], "Judge unable to decide. Using first version."

    def judge_interview_questions(
        self,
        versions: List[Dict[str, Any]],
        job_description: str,
        resume_context: str
    ) -> Dict[str, Any]:
        """
        Evaluate and select best interview questions generation.

        Args:
            versions: List of 3 interview questions outputs (structured)
            job_description: Original job description
            resume_context: Candidate's resume context

        Returns:
            (selected_questions_data, justification_text)
        """
        if len(versions) == 0:
            raise ValueError("No versions to judge")

        if len(versions) == 1:
            return versions[0]

        # Create comparison prompt
        prompt = self._create_interview_questions_judge_prompt(
            versions, job_description, resume_context
        )

        try:
            # Call AI to judge
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse judge's decision
            decision = self._parse_judge_response(response)

            # Judge selected a specific version
            selected_idx = decision.get("selected", 0)
            if 0 <= selected_idx < len(versions):
                return versions[selected_idx]

        except Exception as e:
            # On judge failure, return first version
            console.print(f"[yellow]Judge evaluation failed: {str(e)}. Using first version.[/yellow]")
            return versions[0]

        # Fallback to first version
        return versions[0]

    def _create_cover_letter_judge_prompt(
        self,
        versions: List[Dict[str, Any]],
        job_description: str,
        job_details: Dict[str, Any],
        resume_context: str,
    ) -> str:
        """Create prompt for judging cover letter versions."""
        company = job_details.get("company", "the company")
        position = job_details.get("position", "this position")

        prompt = f"""You are an expert hiring manager with 15+ years of experience evaluating candidates. Your task is to judge which of 3 AI-generated cover letter versions is the best.

**Candidate's Resume:**
{resume_context}

**Job Description:**
Position: {position} at {company}

{job_description[:1000]}

**Instructions:**
Evaluate each version on these FOUR criteria (weighted equally):
1. **Professional Polish**: Grammar, flow, tone, clarity, and professional formatting
2. **Job Alignment**: How well it addresses the position requirements and company
3. **Authenticity**: Sounds genuine and truthful, not robotic or exaggerated
4. **Impact**: Compelling value proposition, memorable, makes candidate stand out

**Cover Letter Versions:**
"""

        for i, version in enumerate(versions, 1):
            prompt += f"\n--- Version {i} ---\n"
            prompt += f"Opening: {version.get('opening_hook', 'N/A')[:200]}\n"
            prompt += f"Summary: {version.get('professional_summary', 'N/A')[:300]}\n"
            prompt += f"Achievements: {json.dumps(version.get('key_achievements', []), indent=2)}\n"
            prompt += f"Skills: {json.dumps(version.get('skills_highlight', []), indent=2)}\n"
            if version.get("company_alignment"):
                prompt += f"Alignment: {version['company_alignment'][:200]}\n"

        prompt += """
**Decision Format:**
Return ONLY a JSON object with these exact keys:
{
  "selected": 0, 1, or 2 (which version is best, or 0 if you want to combine),
  "action": "select" or "combine",
  "justification": "2-3 sentences explaining your choice",
  "scores": {
    "version1": {"polish": 1-10, "alignment": 1-10, "authenticity": 1-10, "impact": 1-10},
    "version2": {...},
    "version3": {...}
  },
  "selection": {  // ONLY if action="combine", specify which parts from which version
    "opening_hook": 1,  // which version's opening to use (1, 2, or 3)
    "professional_summary": 1,
    "key_achievements": 2,
    "skills_highlight": 1,
    "company_alignment": 2
  }
}

Return ONLY valid JSON, nothing else."""

        return prompt

    def _create_resume_judge_prompt(
        self, versions: List[Dict[str, Any]], job_description: str, resume_context: str
    ) -> str:
        """Create prompt for judging resume customization versions."""
        prompt = f"""You are an expert technical recruiter and hiring manager. Your task is to judge which of 3 AI-generated resume customizations is the best.

**Job Description:**
{job_description[:1000]}

**Candidate's Resume Context:**
{resume_context[:500]}

**Instructions:**
Evaluate each version on these FOUR criteria (weighted equally):
1. **Professional Polish**: Clean formatting, clear descriptions, appropriate emphasis
2. **Job Alignment**: How well it emphasizes relevant experience and skills for this role
3. **Authenticity**: Truthful representation, no exaggeration, maintains candidate's voice
4. **Impact**: Effectively highlights achievements and value proposition

**Resume Customization Versions:**
"""

        for i, version in enumerate(versions, 1):
            prompt += f"\n--- Version {i} ---\n"
            prompt += f"Keywords: {version.get('keywords', [])}\n"
            # Show first few bullet reorders as sample
            bullet_orders = version.get("bullet_reorder", {})
            for job, bullets in list(bullet_orders.items())[:2]:
                prompt += f"  {job}: {bullets[:3]}...\n"

        prompt += """
**Decision Format:**
Return ONLY a JSON object with these exact keys:
{
  "selected": 0, 1, or 2 (which version is best, or 0 if you want to combine),
  "action": "select" or "combine",
  "justification": "2-3 sentences explaining your choice",
  "scores": {
    "version1": {"polish": 1-10, "alignment": 1-10, "authenticity": 1-10, "impact": 1-10},
    "version2": {...},
    "version3": {...}
  },
  "selection": {  // ONLY if action="combine"
    "keywords": 1,  // which version's keywords to use
    "bullet_reorder": 2  // which version's reordering to use
  }
}

Return ONLY valid JSON, nothing else."""

        return prompt

    def _create_resume_text_judge_prompt(
        self, versions: List[str], job_description: str, base_resume: str
    ) -> str:
        """Create prompt for judging full resume text versions."""
        prompt = f"""You are an expert technical recruiter and hiring manager. Your task is to judge which of 3 AI-generated resume versions is the best.

**Job Description:**
{job_description[:1000]}

**Original Base Resume (for reference):**
{base_resume[:1000]}

**Instructions:**
Evaluate each version on these FOUR criteria (weighted equally):
1. **Professional Polish**: Clean formatting, clear descriptions, appropriate emphasis, proper grammar
2. **Job Alignment**: How well it emphasizes relevant experience and skills for this role
3. **Authenticity**: Truthful representation, no exaggeration, maintains candidate's voice
4. **Impact**: Effectively highlights achievements and value proposition

**Resume Versions:**
"""

        for i, version in enumerate(versions, 1):
            # Show first 1500 chars of each resume for comparison
            prompt += f"\n--- Version {i} ---\n"
            prompt += version[:1500]
            if len(version) > 1500:
                prompt += "\n... (truncated)"
            prompt += "\n"

        prompt += """
**Decision Format:**
Return ONLY a JSON object with these exact keys:
{
  "selected": 0, 1, or 2 (which version is best - use 0, 1, or 2),
  "justification": "2-3 sentences explaining your choice",
  "scores": {
    "version1": {"polish": 1-10, "alignment": 1-10, "authenticity": 1-10, "impact": 1-10},
    "version2": {...},
    "version3": {...}
  }
}

Return ONLY valid JSON, nothing else."""

        return prompt

    def _create_interview_questions_judge_prompt(
        self,
        versions: List[Dict[str, Any]],
        job_description: str,
        resume_context: str
    ) -> str:
        """Create prompt for judging interview questions generation versions."""
        prompt = f"""You are an expert technical interviewer and career coach. Your task is to judge which of 3 AI-generated interview question sets is best.

**Job Description:**
{job_description[:1000]}

**Candidate's Resume Context:**
{resume_context[:500]}

**Instructions:**
Evaluate each version on these FOUR criteria (weighted equally):
1. **Relevance**: Questions align with job requirements and candidate's experience
2. **Quality**: Questions are well-formulated, clear, and appropriate for the role
3. **Coverage**: Good mix of technical, behavioral, and system design questions
4. **Answer Quality**: Provided answers are helpful, accurate, and actionable

**Interview Questions Versions:**
"""

        for i, version in enumerate(versions, 1):
            prompt += f"\n--- Version {i} ---\n"

            job_analysis = version.get("job_analysis", {})
            prompt += f"Role Type: {job_analysis.get('role_type', 'Unknown')}\n"
            prompt += f"Key Technologies: {job_analysis.get('key_technologies', [])}\n"

            tech_questions = version.get("technical_questions", [])
            prompt += f"Technical Questions: {len(tech_questions)}\n"
            for q in tech_questions[:2]:
                prompt += f"  - [{q.get('priority', 'medium')}] {q.get('question', '')[:80]}...\n"

            behavioral_questions = version.get("behavioral_questions", [])
            prompt += f"Behavioral Questions: {len(behavioral_questions)}\n"
            for q in behavioral_questions[:2]:
                prompt += f"  - [{q.get('priority', 'medium')}] {q.get('question', '')[:80]}...\n"

            sys_design = version.get("system_design_questions")
            if sys_design:
                prompt += f"System Design Questions: {len(sys_design)}\n"
            else:
                prompt += "System Design Questions: None\n"

        prompt += """
**Decision Format:**
Return ONLY a JSON object with these exact keys:
{
  "selected": 0, 1, or 2 (which version is best - use 0, 1, or 2),
  "justification": "2-3 sentences explaining your choice",
  "scores": {
    "version1": {"relevance": 1-10, "quality": 1-10, "coverage": 1-10, "answer_quality": 1-10},
    "version2": {...},
    "version3": {...}
  }
}

Return ONLY valid JSON, nothing else."""

        return prompt

    def _parse_judge_response(self, response: str) -> Dict[str, Any]:
        """Parse the judge's JSON response."""
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        return {
            "selected": 0,
            "action": "select",
            "justification": "Failed to parse judge response",
        }

    def _combine_versions(
        self, versions: List[Dict[str, Any]], selection: Dict[str, int]
    ) -> Dict[str, Any]:
        """Combine elements from multiple versions based on judge's selection."""
        combined = {}
        for key, version_idx in selection.items():
            idx = version_idx - 1  # Convert to 0-indexed
            if 0 <= idx < len(versions):
                combined[key] = versions[idx].get(key)
        return combined

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


def create_ai_judge(client, provider: str, config) -> AIJudge:
    """
    Factory function to create an AIJudge instance.

    Args:
        client: Anthropic or OpenAI client
        provider: 'anthropic' or 'openai'
        config: Config object

    Returns:
        AIJudge instance
    """
    return AIJudge(client, provider, config)
