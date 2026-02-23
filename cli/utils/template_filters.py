"""Jinja2 template filters for resume CLI."""

import re

from markupsafe import Markup

# LaTeX special character replacements
LATEX_REPLACEMENTS = {
    # Escape characters that have special meaning in LaTeX
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    # { and } are handled separately in the regex construction
    "~": r"\textasciitilde{}",
    "^": r"\^{}",
    "™": r"\textsuperscript{TM}",
    "®": r"\textsuperscript{R}",
    "©": r"\textcopyright{}",
    "°": r"\textsuperscript{\textdegree}{}",
    "±": r"$\pm$",
    "≥": r"$\ge$",
    "≤": r"$\le$",
    "→": r"$\rightarrow$",
    "—": r"---",  # em dash
    "–": r"--",  # en dash
    # ASCII equivalents for math symbols and arrows
    ">=": r"$\ge$",
    "<=": r"$\le$",
    "->": r"$\rightarrow$",
    "[": r"{[}",
    "]": r"{]}",
}

# Pre-compile regex patterns for performance
LATEX_ESCAPE_REPLACEMENTS = LATEX_REPLACEMENTS.copy()
LATEX_ESCAPE_REPLACEMENTS.update(
    {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
    }
)

# Sort by length descending to match longest first
_keys = sorted(LATEX_ESCAPE_REPLACEMENTS.keys(), key=len, reverse=True)
_pattern = "|".join(map(re.escape, _keys))
LATEX_ESCAPE_PATTERN = re.compile(_pattern)
MARKDOWN_BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")

# Words to keep lowercase in titles
TITLE_SMALL_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "for",
    "nor",
    "so",
    "yet",
    "at",
    "by",
    "in",
    "of",
    "on",
    "to",
    "up",
    "as",
    "with",
}


def latex_escape(text):
    """Escape special LaTeX characters and convert Markdown bold to LaTeX."""
    if text is None:
        return Markup("")

    # If already Markup, return as is to prevent double escaping
    if isinstance(text, Markup):
        return text

    text = str(text)

    # 1. Convert "degrees" to degree symbol
    text = text.replace("degrees", "°")

    # 2. Use pre-compiled patterns for replacement
    def replace(match):
        return LATEX_ESCAPE_REPLACEMENTS[match.group(0)]

    text = LATEX_ESCAPE_PATTERN.sub(replace, text)

    # 3. Convert Markdown bold (**text**) to LaTeX \textbf{text}
    text = MARKDOWN_BOLD_PATTERN.sub(r"\\textbf{\1}", text)

    return Markup(text)  # nosec B704


def proper_title(text):
    """Convert to title case with lowercase for small words (except first word)."""
    if not text:
        return text

    words = text.replace("_", " ").split()
    if not words:
        return text
    # Capitalize first word always
    result = [words[0].capitalize()]
    # Capitalize rest, except small words
    for word in words[1:]:
        if word.lower() in TITLE_SMALL_WORDS:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    return " ".join(result)
