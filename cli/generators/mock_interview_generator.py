"""AI-powered mock interview mode with interactive questioning and response evaluation."""

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
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
from .interview_questions_generator import InterviewQuestionsGenerator
from .template import TemplateGenerator


@dataclass
class InterviewResponse:
    """A user's response to an interview question."""

    question: str
    question_type: str  # technical, behavioral, system_design
    response: str
    evaluation: Optional[Dict[str, Any]] = None
    rating: Optional[int] = None  # 1-5 scale
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class InterviewSession:
    """A mock interview session."""

    session_id: str
    job_description: str
    questions: List[Dict[str, Any]]
    responses: List[InterviewResponse] = field(default_factory=list)
    category: str = "mixed"  # technical, behavioral, mixed
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    overall_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "job_description": self.job_description,
            "questions": self.questions,
            "responses": [
                {
                    "question": r.question,
                    "question_type": r.question_type,
                    "response": r.response,
                    "evaluation": r.evaluation,
                    "rating": r.rating,
                    "timestamp": r.timestamp,
                }
                for r in self.responses
            ],
            "category": self.category,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "overall_score": self.overall_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewSession":
        """Create from dictionary."""
        responses = [
            InterviewResponse(
                question=r["question"],
                question_type=r["question_type"],
                response=r["response"],
                evaluation=r.get("evaluation"),
                rating=r.get("rating"),
                timestamp=r.get("timestamp", datetime.now().isoformat()),
            )
            for r in data.get("responses", [])
        ]
        return cls(
            session_id=data["session_id"],
            job_description=data["job_description"],
            questions=data["questions"],
            responses=responses,
            category=data.get("category", "mixed"),
            started_at=data.get("started_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            overall_score=data.get("overall_score"),
        )


class MockInterviewGenerator:
    """Interactive mock interview with AI evaluation."""

    def __init__(self, yaml_path: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize mock interview generator.

        Args:
            yaml_path: Path to resume.yaml
            config: Configuration object
        """
        self.config = config or Config()
        self.yaml_path = yaml_path
        self.yaml_handler = ResumeYAML(yaml_path)
        self.template_generator = TemplateGenerator(yaml_path, config=config)

        # Initialize interview questions generator
        self.questions_generator = InterviewQuestionsGenerator(yaml_path, config=config)

        # Storage for sessions
        self.sessions_dir = Path.home() / ".resume-cli" / "interview_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

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
            client_kwargs: Dict[str, Any] = {"api_key": api_key}
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

    def start_session(
        self,
        job_description: str,
        variant: str = "base",
        category: str = "mixed",
        num_technical: int = 5,
        num_behavioral: int = 3,
        include_system_design: bool = True,
    ) -> InterviewSession:
        """
        Start a new mock interview session.

        Args:
            job_description: Job description text
            variant: Resume variant to use
            category: Question category (technical, behavioral, mixed)
            num_technical: Number of technical questions
            num_behavioral: Number of behavioral questions
            include_system_design: Include system design questions

        Returns:
            InterviewSession object
        """
        console.print("[bold blue]Starting Mock Interview Session[/bold blue]")

        # Generate questions based on category
        if category == "technical":
            num_behavioral = 0
            include_system_design = False
        elif category == "behavioral":
            num_technical = 0
            include_system_design = False

        # Generate questions
        questions_data = self.questions_generator.generate(
            job_description=job_description,
            variant=variant,
            num_technical=num_technical,
            num_behavioral=num_behavioral,
            include_system_design=include_system_design,
        )

        # Build questions list
        questions = []

        # Add technical questions
        for q in questions_data.get("technical_questions", []):
            questions.append(
                {
                    "question": q.get("question", ""),
                    "type": "technical",
                    "category": q.get("category", ""),
                    "priority": q.get("priority", "medium"),
                    "context": q.get("context", ""),
                    "reference": q.get("reference", ""),
                    "answer": q.get("answer", ""),  # Ideal answer for reference
                    "tips": q.get("tips", []),
                }
            )

        # Add behavioral questions
        for q in questions_data.get("behavioral_questions", []):
            questions.append(
                {
                    "question": q.get("question", ""),
                    "type": "behavioral",
                    "framework": q.get("framework", "STAR Method"),
                    "priority": q.get("priority", "medium"),
                    "context": q.get("context", ""),
                    "reference": q.get("reference", ""),
                    "answer": q.get("answer", ""),
                    "tips": q.get("tips", []),
                }
            )

        # Add system design questions
        for q in questions_data.get("system_design_questions", []):
            questions.append(
                {
                    "question": q.get("question", ""),
                    "type": "system_design",
                    "complexity": q.get("complexity", "medium"),
                    "key_areas": q.get("key_areas", []),
                    "context": q.get("context", ""),
                    "reference": q.get("reference", ""),
                    "talking_points": q.get("talking_points", []),
                }
            )

        # Shuffle questions for variety
        import random

        random.shuffle(questions)

        # Create session
        session = InterviewSession(
            session_id=str(uuid.uuid4())[:8],
            job_description=job_description,
            questions=questions,
            category=category,
        )

        # Save session
        self._save_session(session)

        console.print(f"[green]✓[/green] Session started with {len(questions)} questions")

        return session

    def evaluate_response(
        self,
        session: InterviewSession,
        question_index: int,
        user_response: str,
    ) -> InterviewResponse:
        """
        Evaluate a user's response to a question.

        Args:
            session: Current interview session
            question_index: Index of the question being answered
            user_response: User's response text

        Returns:
            InterviewResponse with evaluation
        """
        if question_index >= len(session.questions):
            raise ValueError(f"Question index {question_index} out of range")

        question = session.questions[question_index]

        # Get evaluation from AI
        evaluation = self._evaluate_with_ai(
            question=question,
            user_response=user_response,
            question_type=question.get("type", "technical"),
        )

        # Create response object
        response = InterviewResponse(
            question=question.get("question", ""),
            question_type=question.get("type", "technical"),
            response=user_response,
            evaluation=evaluation,
            rating=evaluation.get("rating", 3),
        )

        # Add to session
        session.responses.append(response)

        # Save updated session
        self._save_session(session)

        return response

    def _evaluate_with_ai(
        self,
        question: Dict[str, Any],
        user_response: str,
        question_type: str,
    ) -> Dict[str, Any]:
        """Evaluate response using AI."""
        prompt = self._build_evaluation_prompt(question, user_response, question_type)

        try:
            if self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                response = self._call_openai(prompt)

            # Extract evaluation from response
            evaluation = self._parse_evaluation(response)
            return evaluation

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] AI evaluation failed: {str(e)}")
            return {
                "rating": 3,
                "strengths": ["Response provided"],
                "improvements": ["Unable to analyze - AI evaluation failed"],
                "suggestions": ["Review the question and try again"],
                "score_breakdown": {
                    "correctness": 3,
                    "depth": 3,
                    "examples": 3,
                    "clarity": 3,
                },
            }

    def _build_evaluation_prompt(
        self,
        question: Dict[str, Any],
        user_response: str,
        question_type: str,
    ) -> str:
        """Build prompt for response evaluation."""

        if question_type == "technical":
            prompt = f"""You are an expert technical interviewer. Evaluate the candidate's response to the following technical interview question.

Question: {question.get('question', '')}
Category: {question.get('category', 'Technical')}
Context: {question.get('context', '')}

Candidate's Response:
{user_response}

Ideal Answer/Key Points:
{question.get('answer', '')}

Tips mentioned:
{', '.join(question.get('tips', []))}

Evaluate this response and provide:
1. Overall rating (1-5 scale)
2. Key strengths in the response
3. Areas for improvement
4. Specific suggestions to improve the answer
5. A breakdown of scores: correctness, depth, examples, clarity (each 1-5)

Return ONLY valid JSON with this exact structure:
{{
  "rating": 4,
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "score_breakdown": {{
    "correctness": 4,
    "depth": 3,
    "examples": 5,
    "clarity": 4
  }}
}}

Return ONLY the JSON:"""

        elif question_type == "behavioral":
            framework = question.get("framework", "STAR Method")
            prompt = f"""You are an expert behavioral interviewer. Evaluate the candidate's response to the following behavioral interview question using the {framework} framework.

Question: {question.get('question', '')}
Framework: {framework}
Context: {question.get('context', '')}

Candidate's Response:
{user_response}

Ideal Answer/Key Points:
{question.get('answer', '')}

Tips mentioned:
{', '.join(question.get('tips', []))}

Evaluate this response and provide:
1. Overall rating (1-5 scale)
2. How well they followed the {framework} framework
3. Key strengths in the response
4. Areas for improvement
5. Specific suggestions to improve the answer
6. A breakdown of scores: star_structure, specificity, impact, reflection (each 1-5)

Return ONLY valid JSON with this exact structure:
{{
  "rating": 4,
  "framework_score": 4,
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "score_breakdown": {{
    "star_structure": 4,
    "specificity": 5,
    "impact": 4,
    "reflection": 3
  }}
}}

Return ONLY the JSON:"""

        else:  # system_design
            prompt = f"""You are an expert system design interviewer. Evaluate the candidate's response to the following system design question.

Question: {question.get('question', '')}
Complexity: {question.get('complexity', 'medium')}
Key Areas to Discuss: {', '.join(question.get('key_areas', []))}
Context: {question.get('context', '')}

Candidate's Response:
{user_response}

Talking Points:
{', '.join(question.get('talking_points', []))}

Evaluate this response and provide:
1. Overall rating (1-5 scale)
2. Key strengths in the response
3. Areas for improvement
4. Specific suggestions to improve the answer
5. A breakdown of scores: scalability, consistency, availability, clarity (each 1-5)

Return ONLY valid JSON with this exact structure:
{{
  "rating": 4,
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "score_breakdown": {{
    "scalability": 4,
    "consistency": 3,
    "availability": 4,
    "clarity": 5
  }}
}}

Return ONLY the JSON:"""

        return prompt

    def _parse_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse AI evaluation response."""
        import re

        # Try to extract JSON
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object
        obj_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        # Default evaluation if parsing fails
        return {
            "rating": 3,
            "strengths": ["Response provided"],
            "improvements": ["Unable to analyze response"],
            "suggestions": ["Try to be more specific with examples"],
            "score_breakdown": {"correctness": 3, "depth": 3, "examples": 3, "clarity": 3},
        }

    def complete_session(self, session: InterviewSession) -> Dict[str, Any]:
        """
        Complete an interview session and generate summary.

        Args:
            session: Interview session to complete

        Returns:
            Summary dict with overall statistics
        """
        session.completed_at = datetime.now().isoformat()

        # Calculate overall score
        if session.responses:
            total_rating = sum(r.rating or 0 for r in session.responses)
            session.overall_score = total_rating / len(session.responses)

        # Save final session
        self._save_session(session)

        # Generate summary
        summary = self.generate_session_summary(session)

        return summary

    def generate_session_summary(self, session: InterviewSession) -> Dict[str, Any]:
        """Generate summary statistics for a session."""
        total_questions = len(session.questions)
        answered = len(session.responses)

        if not session.responses:
            return {
                "session_id": session.session_id,
                "total_questions": total_questions,
                "answered": 0,
                "overall_score": 0,
                "category": session.category,
            }

        # Calculate category-specific scores
        technical_scores = []
        behavioral_scores = []
        system_design_scores = []

        for response in session.responses:
            if response.rating:
                if response.question_type == "technical":
                    technical_scores.append(response.rating)
                elif response.question_type == "behavioral":
                    behavioral_scores.append(response.rating)
                elif response.question_type == "system_design":
                    system_design_scores.append(response.rating)

        return {
            "session_id": session.session_id,
            "total_questions": total_questions,
            "answered": answered,
            "overall_score": session.overall_score or 0,
            "technical_score": (
                sum(technical_scores) / len(technical_scores) if technical_scores else 0
            ),
            "behavioral_score": (
                sum(behavioral_scores) / len(behavioral_scores) if behavioral_scores else 0
            ),
            "system_design_score": (
                sum(system_design_scores) / len(system_design_scores) if system_design_scores else 0
            ),
            "category": session.category,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        }

    def render_session_report(self, session: InterviewSession) -> str:
        """Render session results as Markdown report."""
        lines = []

        lines.append("# Mock Interview Session Report")
        lines.append(f"**Session ID:** {session.session_id}")
        lines.append(f"**Date:** {session.started_at[:10]}")
        lines.append(f"**Category:** {session.category.title()}")
        lines.append("")

        # Summary stats
        summary = self.generate_session_summary(session)

        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"- **Questions Answered:** {summary['answered']} / {summary['total_questions']}"
        )
        lines.append(f"- **Overall Score:** {summary['overall_score']:.1f}/5")
        lines.append("")

        if summary["technical_score"] > 0:
            lines.append(f"- **Technical Score:** {summary['technical_score']:.1f}/5")
        if summary["behavioral_score"] > 0:
            lines.append(f"- **Behavioral Score:** {summary['behavioral_score']:.1f}/5")
        if summary["system_design_score"] > 0:
            lines.append(f"- **System Design Score:** {summary['system_design_score']:.1f}/5")

        lines.append("")

        # Detailed responses
        lines.append("## Detailed Responses")
        lines.append("")

        for i, response in enumerate(session.responses, 1):
            question = session.questions[i - 1] if i <= len(session.questions) else {}

            lines.append(f"### Question {i}: {response.question_type.title()}")
            lines.append("")
            lines.append(f"**Q:** {response.question}")
            lines.append("")
            lines.append(f"**Your Answer:** {response.response}")
            lines.append("")

            if response.evaluation:
                lines.append(f"**Rating:** {response.rating}/5")
                lines.append("")

                if response.evaluation.get("strengths"):
                    lines.append("**Strengths:**")
                    for s in response.evaluation["strengths"]:
                        lines.append(f"- {s}")
                    lines.append("")

                if response.evaluation.get("improvements"):
                    lines.append("**Areas for Improvement:**")
                    for imp in response.evaluation["improvements"]:
                        lines.append(f"- {imp}")
                    lines.append("")

                if response.evaluation.get("suggestions"):
                    lines.append("**Suggestions:**")
                    for sug in response.evaluation["suggestions"]:
                        lines.append(f"- {sug}")
                    lines.append("")

                # Show ideal answer for reference
                if question.get("answer") and question.get("type") != "system_design":
                    lines.append("**Ideal Answer:**")
                    lines.append(question["answer"])
                    lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved interview sessions."""
        sessions = []

        for file in self.sessions_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                sessions.append(
                    {
                        "session_id": data.get("session_id"),
                        "date": data.get("started_at", "")[:10],
                        "category": data.get("category", "mixed"),
                        "questions": len(data.get("questions", [])),
                        "responses": len(data.get("responses", [])),
                        "overall_score": data.get("overall_score"),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by date descending
        sessions.sort(key=lambda x: x["date"], reverse=True)

        return sessions

    def load_session(self, session_id: str) -> Optional[InterviewSession]:
        """Load a specific session by ID."""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            data = json.loads(session_file.read_text())
            return InterviewSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_session(self, session: InterviewSession) -> None:
        """Save session to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        session_file.write_text(json.dumps(session.to_dict(), indent=2))

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        model = self.config.ai_model

        message = self.client.messages.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 2000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API."""
        model = self.config.ai_model

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=self.config.get("ai.max_tokens", 2000),
            temperature=self.config.get("ai.temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


def start_mock_interview(
    yaml_path: Optional[Path] = None,
    config: Optional[Config] = None,
    job_description: str = "",
    variant: str = "base",
    category: str = "mixed",
    num_technical: int = 5,
    num_behavioral: int = 3,
    include_system_design: bool = True,
) -> InterviewSession:
    """
    Convenience function to start a mock interview session.

    Args:
        yaml_path: Path to resume.yaml
        config: Configuration object
        job_description: Job description text
        variant: Resume variant to use
        category: Question category (technical, behavioral, mixed)
        num_technical: Number of technical questions
        num_behavioral: Number of behavioral questions
        include_system_design: Include system design questions

    Returns:
        InterviewSession object
    """
    generator = MockInterviewGenerator(yaml_path, config)
    return generator.start_session(
        job_description=job_description,
        variant=variant,
        category=category,
        num_technical=num_technical,
        num_behavioral=num_behavioral,
        include_system_design=include_system_design,
    )
