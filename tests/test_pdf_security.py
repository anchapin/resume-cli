import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.generators.template import TemplateGenerator


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
    def test_pdfconverter_timeout(self, mock_popen):
        from cli.pdf.converter import PDFConverter

        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        # We need output_path.exists() to be False for the exception to trigger the return False
        with patch.object(Path, "exists", return_value=False):
            # Also mock _compile_pandoc to avoid falling through
            with patch.object(converter, "_compile_pandoc", return_value=False):
                with self.assertRaises(RuntimeError) as cm:
                    converter.compile("content", Path("output.pdf"))
                self.assertIn("PDF compilation failed", str(cm.exception))

        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdfconverter_arguments(self, mock_popen):
        from cli.pdf.converter import PDFConverter

        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=True):
            converter.compile("content", Path("output.pdf"))

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("-no-shell-escape", command)
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)

    @patch("subprocess.Popen")
    def test_coverlettergenerator_timeout(self, mock_popen):
        from cli.generators.cover_letter_generator import CoverLetterGenerator
        from cli.utils.config import Config

        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        # Setup mock config needed for CoverLetterGenerator
        mock_config = MagicMock(spec=Config)
        mock_config.get.return_value = {}
        mock_config.ai_provider = "anthropic"
        mock_config.ai_provider = "anthropic"

        import os

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock"}):
            generator = CoverLetterGenerator(config=mock_config, resume_data={})

            with patch.object(Path, "exists", return_value=False):
                result = generator._compile_pdf(Path("output.pdf"), "content")

            self.assertFalse(result)
            process_mock.kill.assert_called_once()
            process_mock.communicate.assert_any_call(timeout=30)

    @patch("subprocess.Popen")
    def test_coverlettergenerator_arguments(self, mock_popen):
        from cli.generators.cover_letter_generator import CoverLetterGenerator
        from cli.utils.config import Config

        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        mock_config = MagicMock(spec=Config)
        mock_config.get.return_value = {}
        mock_config.ai_provider = "anthropic"

        import os

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock"}):
            generator = CoverLetterGenerator(config=mock_config, resume_data={})

            with patch.object(Path, "exists", return_value=True):
                result = generator._compile_pdf(Path("output.pdf"), "content")

            self.assertTrue(result)
            args, _ = mock_popen.call_args
            command = args[0]
            self.assertIn("-no-shell-escape", command)
            self.assertIn("-interaction=nonstopmode", command)
            self.assertIn("pdflatex", command)


if __name__ == "__main__":
    unittest.main()
