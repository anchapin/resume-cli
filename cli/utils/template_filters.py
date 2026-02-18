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

    # 2. Build replacements dictionary including \ { }
    replacements = LATEX_REPLACEMENTS.copy()
    replacements["\\"] = r"\textbackslash{}"
    replacements["{"] = r"\{"
    replacements["}"] = r"\}"

    # 3. Build regex pattern (keys sorted by length descending to match longest first)
    # Escape keys to handle regex special characters in the keys themselves
    keys = sorted(replacements.keys(), key=len, reverse=True)
    pattern = "|".join(map(re.escape, keys))

    # 4. Perform single-pass replacement
    def replace(match):
        return replacements[match.group(0)]

    text = re.sub(pattern, replace, text)

    # 5. Convert Markdown bold (**text**) to LaTeX \textbf{text}
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)

    return Markup(text)


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
