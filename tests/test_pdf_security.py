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
        self.ai_provider = "openai"

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
    def test_pdfconverter_pdflatex_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        result = converter._compile_pdflatex(Path("test.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdfconverter_pdflatex_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=True):
            converter._compile_pdflatex(Path("test.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("-no-shell-escape", command)
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdfconverter_pandoc_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        result = converter._compile_pandoc(Path("test.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdfconverter_pandoc_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=True):
            converter._compile_pandoc(Path("test.tex"), Path("output.pdf"), Path("."))

        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)
        self.assertIn("pandoc", command)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "mock", "ANTHROPIC_API_KEY": "mock"})
    @patch("subprocess.Popen")
    def test_coverletter_pdflatex_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})

        result = generator._compile_pdf(Path("output.pdf"), "content")

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "mock", "ANTHROPIC_API_KEY": "mock"})
    @patch("subprocess.Popen")
    def test_coverletter_pdflatex_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})

        with patch.object(Path, "exists", return_value=True):
            generator._compile_pdf(Path("output.pdf"), "content")

        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("-no-shell-escape", command)
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "mock", "ANTHROPIC_API_KEY": "mock"})
    @patch("subprocess.Popen")
    def test_coverletter_pandoc_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]

        # First call pdflatex fails with FileNotFoundError, second call pandoc times out
        def side_effect(*args, **kwargs):
            if args[0][0] == "pdflatex":
                raise FileNotFoundError()
            return process_mock

        mock_popen.side_effect = side_effect

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})

        result = generator._compile_pdf(Path("output.pdf"), "content")

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "mock", "ANTHROPIC_API_KEY": "mock"})
    @patch("subprocess.Popen")
    def test_coverletter_pandoc_arguments(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b"", b"")
        process_mock.returncode = 0

        def side_effect(*args, **kwargs):
            if args[0][0] == "pdflatex":
                raise FileNotFoundError()
            return process_mock

        mock_popen.side_effect = side_effect

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})

        with patch.object(Path, "exists", side_effect=[False, False, True, True]):
            generator._compile_pdf(Path("output.pdf"), "content")

        # mock_popen gets called twice, once for pdflatex, once for pandoc
        # The last call is pandoc
        args, _ = mock_popen.call_args
        command = args[0]

        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)
        self.assertIn("pandoc", command)


if __name__ == "__main__":
    unittest.main()
