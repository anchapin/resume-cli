"""
PDF Converter Module

Provides PDF conversion utilities using pdflatex or pandoc.
This module extracts and consolidates the PDF compilation logic from the existing
TemplateGenerator class.
"""

import subprocess
from pathlib import Path
from typing import Optional


class PDFConverter:
    """
    Handles conversion of LaTeX content to PDF format.
    
    This class provides methods to compile LaTeX to PDF using either
    pdflatex (preferred) or pandoc as a fallback.
    """

    def __init__(self):
        """Initialize the PDF converter."""
        pass

    def compile(
        self,
        tex_content: str,
        output_path: Path,
        working_dir: Optional[Path] = None,
    ) -> None:
        """
        Compile LaTeX content to PDF.
        
        Args:
            tex_content: LaTeX content as string
            output_path: Path for the output PDF file
            working_dir: Working directory for compilation (defaults to output_path parent)
            
        Raises:
            RuntimeError: If PDF compilation fails
        """
        output_path = Path(output_path)
        
        # Create temporary .tex file
        tex_path = output_path.with_suffix(".tex")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        # Determine working directory
        if working_dir is None:
            working_dir = tex_path.parent

        # Try pdflatex first
        pdf_created = self._compile_pdflatex(tex_path, output_path, working_dir)
        
        if not pdf_created or not output_path.exists():
            # Fallback to pandoc
            pdf_created = self._compile_pandoc(tex_path, output_path, working_dir)

        if not pdf_created or not output_path.exists():
            raise RuntimeError(
                "PDF compilation failed. Please install pdflatex or pandoc.\n"
                "  Ubuntu/Debian: sudo apt-get install texlive-full\n"
                "  macOS: brew install mactex\n"
                "  Or export as Markdown instead."
            )

    def _compile_pdflatex(
        self,
        tex_path: Path,
        output_path: Path,
        working_dir: Path,
    ) -> bool:
        """
        Compile LaTeX to PDF using pdflatex.
        
        Args:
            tex_path: Path to the .tex file
            output_path: Path for the output PDF
            working_dir: Working directory for compilation
            
        Returns:
            True if PDF was created successfully
        """
        try:
            process = subprocess.Popen(
                ["pdflatex", "-interaction=nonstopmode", tex_path.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 or output_path.exists():
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Check if PDF was created anyway (pdflatex returns non-zero for warnings)
            if output_path.exists():
                return True
        
        return False

    def _compile_pandoc(
        self,
        tex_path: Path,
        output_path: Path,
        working_dir: Path,
    ) -> bool:
        """
        Compile LaTeX to PDF using pandoc as fallback.
        
        Args:
            tex_path: Path to the .tex file
            output_path: Path for the output PDF
            working_dir: Working directory for compilation
            
        Returns:
            True if PDF was created successfully
        """
        try:
            process = subprocess.Popen(
                ["pandoc", str(tex_path), "-o", str(output_path), "--pdf-engine=xelatex"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 or output_path.exists():
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return False

    def is_pdflatex_available(self) -> bool:
        """
        Check if pdflatex is available on the system.
        
        Returns:
            True if pdflatex is available
        """
        try:
            process = subprocess.Popen(
                ["pdflatex", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            return False

    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available on the system.
        
        Returns:
            True if pandoc is available
        """
        try:
            process = subprocess.Popen(
                ["pandoc", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            return False

    def get_available_engine(self) -> Optional[str]:
        """
        Get the first available PDF compilation engine.
        
        Returns:
            Name of available engine ('pdflatex' or 'pandoc'), or None if neither is available
        """
        if self.is_pdflatex_available():
            return "pdflatex"
        if self.is_pandoc_available():
            return "pandoc"
        return None
