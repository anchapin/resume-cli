import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.generators.template import TemplateGenerator
from cli.pdf.converter import PDFConverter
from cli.generators.cover_letter_generator import CoverLetterGenerator


class MockConfig:
    def get(self, *args, **kwargs):
        return {}

    @property
    def ai_provider(self):
        return "anthropic"

    @property
    def anthropic_api_key(self):
        return "mock"

    @property
    def output_dir(self):
        return Path("/tmp")

    @property
    def ai_model(self):
        return "mock"


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
    def test_pdf_converter_pdflatex_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pdflatex", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()
        result = converter._compile_pdflatex(Path("output.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdf_converter_pandoc_timeout(self, mock_popen):
        process_mock = MagicMock()
        process_mock.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
            (b"", b""),
        ]
        mock_popen.return_value = process_mock

        converter = PDFConverter()
        result = converter._compile_pandoc(Path("output.tex"), Path("output.pdf"), Path("."))

        self.assertFalse(result)
        process_mock.kill.assert_called_once()
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdf_converter_pdflatex_arguments(self, mock_popen):
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
        self.assertIn("-interaction=nonstopmode", command)
        self.assertIn("pdflatex", command)
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("cli.pdf.converter.subprocess.Popen")
    def test_pdf_converter_pandoc_arguments(self, mock_popen):
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
        self.assertIn("--pdf-engine=xelatex", command)
        self.assertIn("pandoc", command)
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("subprocess.Popen")
    def test_cover_letter_pdflatex_timeout(self, mock_popen):
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

    @patch("subprocess.Popen")
    def test_cover_letter_pandoc_timeout(self, mock_popen):
        # We need to force pdflatex to fail so it falls back to pandoc
        def popen_side_effect(*args, **kwargs):
            mock = MagicMock()
            if "pdflatex" in args[0]:
                mock.returncode = 1
                mock.communicate.return_value = (b"", b"")
            elif "pandoc" in args[0]:
                mock.communicate.side_effect = [
                    subprocess.TimeoutExpired(cmd="pandoc", timeout=30),
                    (b"", b""),
                ]
            return mock

        mock_popen.side_effect = popen_side_effect

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})
        with patch.object(Path, "exists", return_value=False):
            result = generator._compile_pdf(Path("output.pdf"), "content")

        self.assertFalse(result)

    @patch("subprocess.Popen")
    def test_cover_letter_pdflatex_arguments(self, mock_popen):
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
        process_mock.communicate.assert_any_call(timeout=30)

    @patch("subprocess.Popen")
    def test_cover_letter_pandoc_arguments(self, mock_popen):
        # We need to force pdflatex to fail via exception so it falls back to pandoc
        pandoc_mock = MagicMock()
        pandoc_mock.returncode = 0
        pandoc_mock.communicate.return_value = (b"", b"")

        def popen_side_effect(*args, **kwargs):
            if "pdflatex" in args[0]:
                raise FileNotFoundError("pdflatex not found")
            return pandoc_mock

        mock_popen.side_effect = popen_side_effect

        generator = CoverLetterGenerator(config=MockConfig(), resume_data={})

        with patch.object(Path, "exists", side_effect=[False, False, True]):
            generator._compile_pdf(Path("output.pdf"), "content")

        # Find the call to pandoc
        pandoc_call = None
        for call_args in mock_popen.call_args_list:
            args = call_args[0][0]
            if "pandoc" in args:
                pandoc_call = args
                break

        self.assertIsNotNone(pandoc_call)
        self.assertIn("--pdf-engine-opt=-no-shell-escape", pandoc_call)
        self.assertIn("--pdf-engine=xelatex", pandoc_call)


if __name__ == "__main__":
    unittest.main()
