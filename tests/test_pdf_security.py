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


class TestPDFConverterSecurity(unittest.TestCase):
    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdflatex_timeout(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        from cli.pdf.converter import PDFConverter

        converter = PDFConverter()

        # We mock output_path.exists to False to ensure failure
        with patch.object(Path, "exists", return_value=False):
            result = converter._compile_pdflatex(Path("test.tex"), Path("test.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pandoc_timeout(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        from cli.pdf.converter import PDFConverter

        converter = PDFConverter()

        with patch.object(Path, "exists", return_value=False):
            result = converter._compile_pandoc(Path("test.tex"), Path("test.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

        # Verify shell escape argument
        args, _ = mock_popen.call_args
        command = args[0]
        self.assertIn("--pdf-engine-opt=-no-shell-escape", command)


class TestCoverLetterGeneratorSecurity(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_pdflatex_timeout(self, mock_popen):
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        from cli.generators.cover_letter_generator import CoverLetterGenerator

        # Use a properly mocked config
        class MockConfig:
            def __init__(self):
                self.ai_provider = "anthropic"
                self.anthropic_api_key = "test"

            def get(self, *args, **kwargs):
                return {}

        # The class needs yaml_path to be initiated, mocking one
        with patch("cli.generators.cover_letter_generator.ResumeYAML"):
            generator = CoverLetterGenerator(yaml_path=Path("dummy.yaml"), config=MockConfig())

        # Test timeout handling
        with patch.object(Path, "exists", return_value=False):
            result = generator._compile_pdf(Path("output.pdf"), "content")

        # It should return False instead of raising an exception because we only check if output exists and handled timeout gracefully
        self.assertFalse(result)

        # Verify process was killed
        process_mock.kill.assert_called_once()

        # Verify timeout was passed to communicate
        process_mock.communicate.assert_any_call(timeout=30)


if __name__ == "__main__":
    unittest.main()
