from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from helpers import run_echo


def test_leading_dot_and_scientific_literals():
    result = run_echo(
        """
say(.5);
say(1e3);
say(1e-3);
say(.5.type());
say(1e3.type());
say(1e-3.type());
say(1.5e2);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines[0] == "0.5"
    assert result.lines[1] == "1000.0"
    assert result.lines[2] == "0.001"
    assert result.lines[3] == "float"
    assert result.lines[4] == "float"
    assert result.lines[5] == "float"
    assert result.lines[6] == "150.0"


def test_trailing_dot_still_allows_method_call():
    result = run_echo("say(5.asInt());\n")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "5"


def test_range_literals_still_parse():
    result = run_echo(
        """
for i: int in 1..3 {
    say(i);
}
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["1", "2", "3"]


def test_parser_accepts_dot_float_and_scientific():
    program = Parser(Lexer().tokenize("x: float = .5;\ny: float = 1e-3;\n")).parse()
    assert len(program.statements) == 2


def test_parser_accepts_triple_quoted_strings():
    program = Parser(Lexer().tokenize('x: str = """a\nb""";\ny: str = \'\'\'c\nd\'\'\';\n')).parse()
    assert len(program.statements) == 2


def test_multiline_double_and_single_quotes():
    result = run_echo(
        '''
text: str = """hello
world""";
also: str = \'\'\'a
b\'\'\';
say(text);
say(also);
'''
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["hello", "world", "a", "b"]


def test_multiline_interpolation():
    result = run_echo(
        '''
name: str = "Echo";
say("""hi ${name}""");
'''
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "hi Echo"


def test_single_line_newline_still_lex_error():
    result = run_echo('say("oops\nthere");\n')
    assert result.exit_code == 1
    assert "Unterminated string" in result.output or "Syntax Error" in result.output
