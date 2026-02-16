"""Tests for progress indicator utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestProgressManager:
    """Tests for ProgressManager class."""

    def test_init_default(self):
        """Test ProgressManager initialization with defaults."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager()
        assert pm.disabled is False
        assert pm._progress is None
        assert pm._task_id is None

    def test_init_disabled(self):
        """Test ProgressManager initialization with disabled=True."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        assert pm.disabled is True
        assert pm._progress is None

    def test_start_ai_generation_disabled(self):
        """Test start_ai_generation when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.start_ai_generation(total=5)
        assert result is pm  # Returns self for chaining
        assert pm._progress is None

    @patch("cli.utils.progress.Progress")
    def test_start_ai_generation_enabled(self, mock_progress):
        """Test start_ai_generation when enabled."""
        from cli.utils.progress import ProgressManager

        # Create mock progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)

        pm = ProgressManager(disabled=False)
        result = pm.start_ai_generation(total=3)

        assert result is pm
        mock_progress_instance.start.assert_called_once()

    def test_update_ai_generation_disabled(self):
        """Test update_ai_generation when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.update_ai_generation(advance=1)
        assert result is pm

    def test_update_ai_generation_no_progress(self):
        """Test update_ai_generation when no progress started."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=False)
        result = pm.update_ai_generation(advance=1)
        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_stop_ai_generation_disabled(self, mock_progress):
        """Test stop_ai_generation when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.stop_ai_generation()
        assert result is pm
        mock_progress.assert_not_called()

    def test_stop_ai_generation_no_progress(self):
        """Test stop_ai_generation when no progress started."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=False)
        result = pm.stop_ai_generation()
        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_start_github_sync(self, mock_progress):
        """Test start_github_sync progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)

        pm = ProgressManager(disabled=False)
        result = pm.start_github_sync(total=50)

        assert result is pm
        mock_progress_instance.start.assert_called_once()

    def test_start_github_sync_disabled(self):
        """Test start_github_sync when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.start_github_sync(total=50)
        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_update_github_sync(self, mock_progress):
        """Test update_github_sync progress."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)

        pm = ProgressManager(disabled=False)
        pm.start_github_sync(total=50)
        result = pm.update_github_sync(completed=25)

        assert result is pm
        mock_progress_instance.update.assert_called_once()

    @patch("cli.utils.progress.Progress")
    def test_stop_github_sync(self, mock_progress):
        """Test stop_github_sync progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)
        mock_progress_instance.stop = MagicMock()

        pm = ProgressManager(disabled=False)
        pm.start_github_sync(total=50)
        result = pm.stop_github_sync()

        assert result is pm
        mock_progress_instance.stop.assert_called_once()

    @patch("cli.utils.progress.Progress")
    def test_start_package_generation(self, mock_progress):
        """Test start_package_generation progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)

        steps = ["Step 1", "Step 2", "Step 3"]
        pm = ProgressManager(disabled=False)
        result = pm.start_package_generation(steps=steps)

        assert result is pm
        assert hasattr(pm, "_steps")
        assert pm._steps == steps

    def test_start_package_generation_disabled(self):
        """Test start_package_generation when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.start_package_generation()
        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_next_package_step(self, mock_progress):
        """Test next_package_step moves to next step."""
        from cli.utils.progress import ProgressManager

        mock_task = MagicMock()
        mock_task.completed = 0
        mock_task.total = 4
        mock_progress_instance = MagicMock()
        mock_progress_instance.tasks = {1: mock_task}
        mock_progress.return_value = mock_progress_instance

        pm = ProgressManager(disabled=False)
        pm._progress = mock_progress_instance
        pm._task_id = 1
        pm._steps = ["Step 1", "Step 2", "Step 3", "Step 4"]

        result = pm.next_package_step()

        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_next_package_step_custom_name(self, mock_progress):
        """Test next_package_step with custom step name."""
        from cli.utils.progress import ProgressManager

        mock_task = MagicMock()
        mock_task.completed = 0
        mock_task.total = 4
        mock_progress_instance = MagicMock()
        mock_progress_instance.tasks = {1: mock_task}
        mock_progress.return_value = mock_progress_instance

        pm = ProgressManager(disabled=False)
        pm._progress = mock_progress_instance
        pm._task_id = 1

        result = pm.next_package_step(step_name="Custom Step")

        assert result is pm
        mock_progress_instance.update.assert_called_once()

    @patch("cli.utils.progress.Progress")
    def test_stop_package_generation(self, mock_progress):
        """Test stop_package_generation progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)
        mock_progress_instance.stop = MagicMock()

        pm = ProgressManager(disabled=False)
        pm.start_package_generation()
        result = pm.stop_package_generation()

        assert result is pm
        mock_progress_instance.stop.assert_called_once()

    @patch("cli.utils.progress.Progress")
    def test_start_pdf_compilation(self, mock_progress):
        """Test start_pdf_compilation progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)

        pm = ProgressManager(disabled=False)
        result = pm.start_pdf_compilation()

        assert result is pm
        mock_progress_instance.start.assert_called_once()

    def test_start_pdf_compilation_disabled(self):
        """Test start_pdf_compilation when disabled."""
        from cli.utils.progress import ProgressManager

        pm = ProgressManager(disabled=True)
        result = pm.start_pdf_compilation()
        assert result is pm

    @patch("cli.utils.progress.Progress")
    def test_stop_pdf_compilation(self, mock_progress):
        """Test stop_pdf_compilation progress indicator."""
        from cli.utils.progress import ProgressManager

        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance
        mock_progress_instance.start = MagicMock()
        mock_progress_instance.add_task = MagicMock(return_value=1)
        mock_progress_instance.stop = MagicMock()

        pm = ProgressManager(disabled=False)
        pm.start_pdf_compilation()
        result = pm.stop_pdf_compilation()

        assert result is pm
        mock_progress_instance.stop.assert_called_once()


class TestProgressModuleFunctions:
    """Tests for module-level progress functions."""

    def test_get_progress_manager_creates_new(self):
        """Test get_progress_manager creates new instance."""
        from cli.utils import progress

        # Reset global
        progress._progress_manager = None

        pm = progress.get_progress_manager()
        assert pm is not None
        assert isinstance(pm, progress.ProgressManager)

    def test_get_progress_manager_returns_existing(self):
        """Test get_progress_manager returns existing instance."""
        from cli.utils import progress

        # Reset and create specific instance
        progress._progress_manager = None
        pm1 = progress.get_progress_manager()
        pm2 = progress.get_progress_manager()

        assert pm1 is pm2  # Same instance

    def test_get_progress_manager_disabled(self):
        """Test get_progress_manager with disabled=True."""
        from cli.utils import progress

        progress._progress_manager = None
        pm = progress.get_progress_manager(disabled=True)

        assert pm.disabled is True

    def test_disable_progress(self):
        """Test disable_progress sets global to disabled."""
        from cli.utils import progress

        progress._progress_manager = None
        progress.disable_progress()

        assert progress._progress_manager is not None
        assert progress._progress_manager.disabled is True

    def test_enable_progress(self):
        """Test enable_progress resets global."""
        from cli.utils import progress

        progress.disable_progress()
        progress.enable_progress()

        assert progress._progress_manager is None  # Will be recreated
