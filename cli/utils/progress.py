"""Progress indicator utilities for long-running operations."""

from typing import Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)

# Initialize console for output
console = Console()


class ProgressManager:
    """Manages progress indicators for various CLI operations."""

    def __init__(self, disabled: bool = False):
        """
        Initialize progress manager.

        Args:
            disabled: If True, disable all progress indicators
        """
        self.disabled = disabled
        self._progress: Optional[Progress] = None
        self._task_id = None

    def start_ai_generation(self, total: int = 3) -> "ProgressManager":
        """
        Start progress indicator for AI generation.

        Args:
            total: Total number of generations (default: 3)

        Returns:
            Self for chaining
        """
        if self.disabled:
            return self

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            f"[cyan]Generating resume variants ({total}/3)...", total=total
        )

        return self

    def update_ai_generation(self, advance: int = 1) -> "ProgressManager":
        """
        Update AI generation progress.

        Args:
            advance: Number of steps to advance

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress or self._task_id is None:
            return self

        self._progress.update(self._task_id, advance=advance)
        return self

    def stop_ai_generation(self) -> "ProgressManager":
        """
        Stop AI generation progress.

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress:
            return self

        self._progress.stop()
        self._progress = None
        self._task_id = None
        return self

    def start_github_sync(self, total: int = 100) -> "ProgressManager":
        """
        Start progress indicator for GitHub sync.

        Args:
            total: Estimated total repos to fetch

        Returns:
            Self for chaining
        """
        if self.disabled:
            return self

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total} repos)"),
            TimeElapsedColumn(),
            console=console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "[cyan]Fetching GitHub repositories...", total=total
        )

        return self

    def update_github_sync(self, completed: int) -> "ProgressManager":
        """
        Update GitHub sync progress.

        Args:
            completed: Number of repos fetched so far

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress or self._task_id is None:
            return self

        self._progress.update(self._task_id, completed=completed)
        return self

    def stop_github_sync(self) -> "ProgressManager":
        """
        Stop GitHub sync progress.

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress:
            return self

        self._progress.stop()
        self._progress = None
        self._task_id = None
        return self

    def start_package_generation(self, steps: list = None) -> "ProgressManager":
        """
        Start progress indicator for generate-package command.

        Args:
            steps: List of step names (default: standard package generation steps)

        Returns:
            Self for chaining
        """
        if self.disabled:
            return self

        if steps is None:
            steps = [
                "Extracting job details",
                "Generating resume (MD)",
                "Generating resume (PDF)",
                "Generating cover letter",
            ]

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            "[cyan]Generating application package...", total=len(steps)
        )
        self._steps = steps

        return self

    def next_package_step(self, step_name: Optional[str] = None) -> "ProgressManager":
        """
        Move to the next package generation step.

        Args:
            step_name: Optional custom step name (uses next step from list if not provided)

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress or self._task_id is None:
            return self

        current = self._progress.tasks[self._task_id].completed
        total = self._progress.tasks[self._task_id].total

        if step_name:
            description = f"[cyan]{step_name}..."
        elif hasattr(self, "_steps") and current < len(self._steps):
            description = f"[cyan]{self._steps[current]}..."
        else:
            description = f"[cyan]Step {current + 1}/{total}..."

        self._progress.update(self._task_id, advance=1, description=description)
        return self

    def stop_package_generation(self) -> "ProgressManager":
        """
        Stop package generation progress.

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress:
            return self

        self._progress.stop()
        self._progress = None
        self._task_id = None
        return self

    def start_pdf_compilation(self) -> "ProgressManager":
        """
        Start progress indicator for PDF compilation.

        Returns:
            Self for chaining
        """
        if self.disabled:
            return self

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        )
        self._progress.start()
        self._task_id = self._progress.add_task("[cyan]Compiling LaTeX to PDF...")

        return self

    def stop_pdf_compilation(self) -> "ProgressManager":
        """
        Stop PDF compilation progress.

        Returns:
            Self for chaining
        """
        if self.disabled or not self._progress:
            return self

        self._progress.stop()
        self._progress = None
        self._task_id = None
        return self


# Global progress manager instance
_progress_manager: Optional[ProgressManager] = None


def get_progress_manager(disabled: bool = False) -> ProgressManager:
    """
    Get or create the global progress manager.

    Args:
        disabled: If True, create a disabled progress manager

    Returns:
        ProgressManager instance
    """
    global _progress_manager

    if _progress_manager is None or disabled:
        _progress_manager = ProgressManager(disabled=disabled)

    return _progress_manager


def disable_progress() -> None:
    """Globally disable all progress indicators."""
    global _progress_manager
    _progress_manager = ProgressManager(disabled=True)


def enable_progress() -> None:
    """Globally re-enable progress indicators."""
    global _progress_manager
    _progress_manager = None  # Will be recreated on next get_progress_manager() call
