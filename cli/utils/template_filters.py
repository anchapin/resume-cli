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


# Pre-compile regex and replacement map for latex_escape
def _build_latex_escape_pattern():
    """Build the regex pattern and replacement map for latex_escape."""
    replacements = LATEX_REPLACEMENTS.copy()
    replacements["\\"] = r"\textbackslash{}"
    replacements["{"] = r"\{"
    replacements["}"] = r"\}"
    replacements["degrees"] = r"\textsuperscript{\textdegree}{}"

    # Sort keys by length descending to match longest first
    keys = sorted(replacements.keys(), key=len, reverse=True)
    pattern_str = "|".join(map(re.escape, keys))

    return re.compile(pattern_str), replacements


LATEX_ESCAPE_PATTERN, FULL_LATEX_REPLACEMENTS = _build_latex_escape_pattern()
BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")


def latex_escape(text):
    """Escape special LaTeX characters and convert Markdown bold to LaTeX."""
    if text is None:
        return Markup("")

    # If already Markup, return as is to prevent double escaping
    if isinstance(text, Markup):
        return text

    text = str(text)

    # Single-pass replacement using pre-compiled regex
    def replace(match):
        return FULL_LATEX_REPLACEMENTS[match.group(0)]

    text = LATEX_ESCAPE_PATTERN.sub(replace, text)

    # Convert Markdown bold (**text**) to LaTeX \textbf{text}
    text = BOLD_PATTERN.sub(r"\\textbf{\1}", text)

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
