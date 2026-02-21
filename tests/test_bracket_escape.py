from cli.utils.template_filters import latex_escape as cli_latex_escape
from resume_pdf_lib.generator import latex_escape as lib_latex_escape
from markupsafe import Markup

def test_cli_bracket_escape():
    """Test that cli.utils.template_filters.latex_escape escapes [ and ]."""
    input_str = "[Optional]"
    expected = r"{[}Optional{]}"
    assert str(cli_latex_escape(input_str)) == expected

    input_str = r"\item[Optional]"
    expected = r"\textbackslash{}item{[}Optional{]}"
    assert str(cli_latex_escape(input_str)) == expected

def test_lib_bracket_escape():
    """Test that resume_pdf_lib.generator.latex_escape escapes [ and ]."""
    input_str = "[Optional]"
    expected = r"{[}Optional{]}"
    assert str(lib_latex_escape(input_str)) == expected

    input_str = r"\item[Optional]"
    expected = r"\textbackslash{}item{[}Optional{]}"
    assert str(lib_latex_escape(input_str)) == expected
