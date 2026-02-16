"""Jinja2 template filters for resume CLI."""

import re

# LaTeX special character replacements
LATEX_REPLACEMENTS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
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
}

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
    if not text:
        return text

    # First, convert Markdown bold (**text**) to LaTeX \textbf{text}
    # This must happen before character escaping
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)

    # Convert "degrees" to degree symbol first
    text = text.replace("degrees", "°")

    # Escape special characters
    for old, new in LATEX_REPLACEMENTS.items():
        text = text.replace(old, new)

    # Fix up LaTeX commands by unescaping their braces
    # Pattern matches \command\{...\} and converts to \command{...}
    # This handles \textbf, \textsuperscript, \textasciitilde, etc.
    text = re.sub(r"\\([a-zA-Z]+)\\{(.+?)\\}", r"\\\1{\2}", text)

    return text


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
