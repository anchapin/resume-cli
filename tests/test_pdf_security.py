import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.generators.cover_letter_generator import CoverLetterGenerator
from cli.generators.template import TemplateGenerator
from cli.pdf.converter import PDFConverter


class TestPDFSecurity(unittest.TestCase):
    @patch("cli.generators.template.subprocess.Popen")
    def test_pdflatex_timeout(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        # Raise TimeoutExpired on first call, return empty bytes on second call (cleanup)
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        generator = TemplateGenerator()

        # Test timeout handling
        with self.assertRaises(RuntimeError) as cm:
            generator._compile_pdf(Path("output.pdf"), "content")

        self.assertEqual(str(cm.exception), "PDF compilation timed out")

        # Verify process was killed
        process_mock.kill.assert_called_once()

        # Verify timeout was passed to communicate
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.generators.template.subprocess.Popen")
    def test_pdflatex_arguments(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        generator = TemplateGenerator()

        # Run compilation
        # We mock output_path.exists() to return True to avoid RuntimeError
        with patch.object(Path, "exists", return_value=True):
            generator._compile_pdf(Path("output.pdf"), "content")

        # Verify arguments
        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("-no-shell-escape", command)
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_converter_pdflatex_timeout(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        # We need to mock output_path.exists to return False to check fallback/failure
        with patch.object(Path, "exists", return_value=False):
            result = converter._compile_pdflatex(Path("output.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_converter_pdflatex_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=True):
            converter._compile_pdflatex(Path("output.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("-no-shell-escape", command)
        self.assertIn("pdflatex", command)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_converter_pandoc_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=False):
            result = converter._compile_pandoc(Path("output.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_converter_pandoc_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=True):
            converter._compile_pandoc(Path("output.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)
        self.assertIn("pandoc", command)

    @patch("subprocess.Popen")
    def test_cover_letter_pdflatex_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        # Setup env vars so CoverLetterGenerator initializes correctly
        os.environ["ANTHROPIC_API_KEY"] = "mock"

        # We need to mock yaml handler and config properly if we're not initializing fully,
        # but _compile_pdf doesn't rely on `self` heavily. We can just instantiate it.
        # It's better to patch the config to avoid errors
        with patch("cli.generators.cover_letter_generator.Config") as mock_config, patch(
            "cli.generators.cover_letter_generator.ResumeYAML"
        ):

            mock_cfg_inst = mock_config.return_value
            mock_cfg_inst.ai_provider = "anthropic"
            mock_cfg_inst.get.return_value = {}

            generator = CoverLetterGenerator(yaml_path=Path("mock.yaml"), config=mock_cfg_inst)

        with patch.object(Path, "exists", return_value=False):
            result = generator._compile_pdf(Path("output.pdf"), "content")

        # It fails and returns False
        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("subprocess.Popen")
    def test_cover_letter_pdflatex_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        os.environ["ANTHROPIC_API_KEY"] = "mock"
        with patch("cli.generators.cover_letter_generator.Config") as mock_config, patch(
            "cli.generators.cover_letter_generator.ResumeYAML"
        ):

            mock_cfg_inst = mock_config.return_value
            mock_cfg_inst.ai_provider = "anthropic"
            mock_cfg_inst.get.return_value = {}

            generator = CoverLetterGenerator(yaml_path=Path("mock.yaml"), config=mock_cfg_inst)

        with patch.object(Path, "exists", return_value=True):
            generator._compile_pdf(Path("output.pdf"), "content")

        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("-no-shell-escape", command)
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)


if __name__ == "__main__":
    unittest.main()
