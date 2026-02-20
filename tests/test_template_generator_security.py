
import subprocess
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from cli.generators.template import TemplateGenerator

class TestTemplateGeneratorSecurity:
    """Security tests for TemplateGenerator."""

    @patch("subprocess.Popen")
    def test_compile_pdf_uses_timeout(self, mock_popen, tmp_path):
        """Test that _compile_pdf uses a timeout to prevent hanging."""
        # Setup
        gen = TemplateGenerator()
        output_path = tmp_path / "test.pdf"
        tex_content = "dummy content"

        # Mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Run
        try:
            gen._compile_pdf(output_path, tex_content)
        except RuntimeError:
            # We expect RuntimeError because PDF file is not created
            pass

        # Verify communicate was called with timeout
        # Currently this assertion should FAIL because timeout is not used
        mock_process.communicate.assert_called_with(timeout=30)

    @patch("subprocess.Popen")
    def test_compile_pdf_handles_timeout(self, mock_popen, tmp_path):
        """Test that _compile_pdf catches timeout and kills process."""
        # Setup
        gen = TemplateGenerator()
        output_path = tmp_path / "test.pdf"
        tex_content = "dummy content"

        # Mock process that times out
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="pdflatex", timeout=30)
        mock_popen.return_value = mock_process

        # Run
        with pytest.raises(RuntimeError) as excinfo:
            gen._compile_pdf(output_path, tex_content)

        # Verify process was killed
        mock_process.kill.assert_called_once()
