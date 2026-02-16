"""Tests for tutorial commands."""

from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestTutorialsModule:
    """Tests for tutorials module-level functions."""

    def test_tutorials_dict_exists(self):
        """Test that TUTORIALS dictionary is defined."""
        from cli.commands.tutorials import TUTORIALS

        assert isinstance(TUTORIALS, dict)
        assert len(TUTORIALS) > 0

    def test_tutorials_have_required_keys(self):
        """Test that each tutorial has required keys."""
        from cli.commands.tutorials import TUTORIALS

        for key, tutorial in TUTORIALS.items():
            assert "title" in tutorial
            assert "description" in tutorial
            assert "steps" in tutorial
            assert isinstance(tutorial["steps"], list)
            assert len(tutorial["steps"]) > 0

    def test_tutorial_steps_have_required_keys(self):
        """Test that each tutorial step has required keys."""
        from cli.commands.tutorials import TUTORIALS

        for key, tutorial in TUTORIALS.items():
            for step in tutorial["steps"]:
                assert "title" in step
                assert "content" in step


class TestListTutorials:
    """Tests for list_tutorials function."""

    @patch("cli.commands.tutorials.console")
    def test_list_tutorials_calls_print(self, mock_console):
        """Test list_tutorials prints to console."""
        from cli.commands.tutorials import list_tutorials

        list_tutorials()

        # Should have called print multiple times
        assert mock_console.print.call_count > 0


class TestRunTutorial:
    """Tests for run_tutorial function."""

    @patch("cli.commands.tutorials.Prompt")
    @patch("cli.commands.tutorials.Markdown")
    @patch("cli.commands.tutorials.Panel")
    @patch("cli.commands.tutorials.console")
    def test_run_tutorial_valid(self, mock_console, mock_panel, mock_markdown, mock_prompt):
        """Test run_tutorial with valid tutorial key."""
        from cli.commands.tutorials import run_tutorial

        # Mock Prompt.ask to return immediately
        mock_prompt.ask = MagicMock()

        # Mock Panel and Markdown
        mock_panel.return_value = "panel"
        mock_markdown.return_value = "markdown"

        run_tutorial("init")

        # Should have called console.print
        assert mock_console.print.call_count > 0

    @patch("cli.commands.tutorials.console")
    def test_run_tutorial_invalid_key(self, mock_console):
        """Test run_tutorial with invalid tutorial key."""
        from cli.commands.tutorials import run_tutorial

        run_tutorial("nonexistent")

        # Should have printed error message
        mock_console.print.assert_called()

    @patch("cli.commands.tutorials.Prompt")
    @patch("cli.commands.tutorials.Markdown")
    @patch("cli.commands.tutorials.Panel")
    @patch("cli.commands.tutorials.console")
    def test_run_tutorial_generate(self, mock_console, mock_panel, mock_markdown, mock_prompt):
        """Test run_tutorial with generate tutorial."""
        from cli.commands.tutorials import run_tutorial

        mock_prompt.ask = MagicMock()
        mock_panel.return_value = "panel"
        mock_markdown.return_value = "markdown"

        run_tutorial("generate")

        assert mock_console.print.call_count > 0


class TestTutorialCLI:
    """Tests for tutorial CLI commands."""

    def test_tutorial_group_exists(self):
        """Test tutorial group exists."""
        from cli.commands.tutorials import tutorial

        assert tutorial is not None

    def test_tutorial_run_command_invokes(self):
        """Test tutorial run command invokes correctly."""
        from cli.commands.tutorials import tutorial_run

        # Mock the run_tutorial function
        with patch("cli.commands.tutorials.run_tutorial") as _:
            runner = CliRunner()
            result = runner.invoke(tutorial_run, ["init"])
            # Command should execute without crash
            assert result.exit_code == 0


class TestTutorialCLIIntegration:
    """Integration tests for tutorial CLI."""

    def test_tutorial_list_cli(self):
        """Test tutorial list via CLI."""
        from cli.commands.tutorials import tutorial

        runner = CliRunner()
        result = runner.invoke(tutorial, ["list"])

        # Should succeed
        assert result.exit_code == 0

    def test_tutorial_help(self):
        """Test tutorial help."""
        from cli.commands.tutorials import tutorial

        runner = CliRunner()
        result = runner.invoke(tutorial, ["--help"])

        assert result.exit_code == 0
        assert "tutorial" in result.output.lower()
