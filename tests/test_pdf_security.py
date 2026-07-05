import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.generators.template import TemplateGenerator
from cli.pdf.converter import PDFConverter
from cli.generators.cover_letter_generator import CoverLetterGenerator


class MockConfig:
    def __init__(self):
        self.ai_provider = "anthropic"
        self.anthropic_api_key = "mock"
        self.output_dir = Path("output")
        self.ai_model = "claude-3-haiku-20240307"

    def get(self, *args, **kwargs):
        return {}


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
    def test_converter_pdflatex_security(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()
        result = converter._compile_pdflatex(Path("output.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("-no-shell-escape", command)

        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)
        self.assertEqual(process_mock.communicate.call_count, 2)
        self.assertFalse(result)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_converter_pandoc_security(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()
        result = converter._compile_pandoc(Path("output.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)

        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)
        self.assertEqual(process_mock.communicate.call_count, 2)
        self.assertFalse(result)

    @patch("subprocess.Popen")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock"})
    def test_coverletter_pdflatex_security(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})
        result = generator._compile_pdf(Path("output.pdf"), "content")

        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("-no-shell-escape", command)

        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)
        self.assertEqual(process_mock.communicate.call_count, 2)
        self.assertFalse(result)

    @patch("subprocess.Popen")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock"})
    def test_coverletter_pandoc_security(self, mock_popen):
        # We need to test the fallback, so make the first call raise FileNotFoundError
        process_mock_pdflatex = MagicMock()
        process_mock_pandoc = MagicMock()

        process_mock_pandoc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]

        def popen_side_effect(args, **kwargs):
            if args[0] == "pdflatex":
                raise FileNotFoundError("executable not found")
            return process_mock_pandoc

        mock_popen.side_effect = popen_side_effect

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})
        result = generator._compile_pdf(Path("output.pdf"), "content")

        # The last call to Popen should be pandoc
        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)

        process_mock_pandoc.kill.assert_called_once()
        process_mock_pandoc.communicate.assert_any_call(timeout=30)
        self.assertEqual(process_mock_pandoc.communicate.call_count, 2)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
