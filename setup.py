"""Setup configuration for resume-cli."""

from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (
    (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""
)

setup(
    name="resume-cli",
    version="2.0.0",
    author="Alex Chapin",
    author_email="a.n.chapin@gmail.com",
    description="A unified CLI for generating job-specific resumes from YAML",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anchapin/job-hunt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "rich>=13.0.0",
        "pandas>=2.0.0",
        "python-dateutil>=2.8.0",
        "python-dotenv>=1.0.0",
        "python-docx>=0.8.11",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "python-docx>=0.8.11",
    ],
    extras_require={
        "ai": [
            "anthropic>=0.18.0",
            "openai>=1.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "requests>=2.31.0",
            "fastapi>=0.100.0",
            "pydantic>=2.0.0",
            "uvicorn>=0.23.0",
            "httpx>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "resume-cli=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.j2", "config/*.yaml"],
        "resume_pdf_lib": ["*.md"],
    },
)
