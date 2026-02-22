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


if __name__ == "__main__":
    unittest.main()
