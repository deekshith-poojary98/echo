from echo.formatter import format_source
from helpers import run_echo


def _assert_idempotent(source: str) -> str:
    once = format_source(source)
    assert format_source(once) == once
    return once


def test_format_is_idempotent():
    source = """
x:int=1;
if true { say(x); } else { if false { say(2); } else { say(3); } }
for i: int in 1..3 by 1 { say(i); }
"""
    once = format_source(source)
    assert format_source(once) == once
    assert format_source(once) == format_source(format_source(source))


def test_comments_are_kept():
    source = """
// leading
x: int = 1; // trailing
fn foo() {
    // inside
    say(x);
    /* after last */
}
"""
    formatted = _assert_idempotent(source)
    assert "// leading" in formatted
    assert "// trailing" in formatted
    assert "// inside" in formatted
    assert "/* after last */" in formatted
    assert formatted.index("// inside") < formatted.index("say(x);")
    assert formatted.index("say(x);") < formatted.index("/* after last */")
    assert formatted.index("/* after last */") < formatted.index("}")


def test_needed_parens_are_kept():
    formatted = _assert_idempotent("say((1+2)*3); say(1-(2-3)); say(-(1+2));")
    assert "say((1 + 2) * 3);" in formatted
    assert "say(1 - (2 - 3));" in formatted
    assert "say(-(1 + 2));" in formatted


def test_useless_parens_are_dropped():
    formatted = _assert_idempotent("say((1+2)); say((foo()));")
    assert "say(1 + 2);" in formatted
    assert "say(foo());" in formatted
    assert "say((1 + 2));" not in formatted


def test_else_if_is_flattened():
    nested = _assert_idempotent(
        "if true { say(1); } else { if false { say(2); } else { say(3); } }"
    )
    flat = _assert_idempotent(
        "if true { say(1); } else if false { say(2); } else { say(3); }"
    )
    expected = """\
if true {
    say(1);
} else if false {
    say(2);
} else {
    say(3);
}
"""
    assert nested == expected
    assert flat == expected


def test_v06_syntax_formats_stably():
    source = """
fn join(punct: str="!", parts: str...) {
    say(fn(x: int) -> int { return x; }(1));
    xs: list = [1, 2, 3, 4];
    say(xs[1:3]);
    say(xs[1:]);
    say(xs[:2]);
    say(xs[:]);
}
"""
    formatted = _assert_idempotent(source)
    assert "punct: str = \"!\"" in formatted
    assert "parts: str..." in formatted
    assert "fn(x: int) -> int { return x; }" in formatted
    assert "xs[1:3]" in formatted
    assert "xs[1:]" in formatted
    assert "xs[:2]" in formatted
    assert "xs[:]" in formatted


def test_optional_slice_bounds_format_idempotent():
    source = "say(xs[1:]);\nsay(xs[:4]);\nsay(xs[:]);\nsay(xs[1:4]);\n"
    formatted = _assert_idempotent(source)
    assert "xs[1:]" in formatted
    assert "xs[:4]" in formatted
    assert "xs[:]" in formatted
    assert "xs[1:4]" in formatted
    assert "xs[1:xs" not in formatted
    assert "length" not in formatted


def test_for_by_literal_one_is_omitted():
    formatted = _assert_idempotent("for i: int in 1..3 by 1 { say(i); }")
    assert "by 1" not in formatted
    assert "for i: int in 1..3 {" in formatted


def test_import_module_uses_double_quotes():
    formatted = _assert_idempotent("import add from 'math';")
    assert formatted == 'import add from "math";\n'


def test_hash_keys_unquoted_when_identifier():
    formatted = _assert_idempotent('h: hash = { "foo": 1, "a b": 2, "if": 3 };')
    assert formatted == 'h: hash = {foo: 1, "a b": 2, "if": 3};\n'


def test_single_quoted_string_with_double_quotes_is_not_rewritten_broken():
    source = "say('He said \"hi\"');\n"
    formatted = _assert_idempotent(source)
    assert formatted == "say('He said \"hi\"');\n"
    result = run_echo(formatted)
    assert result.exit_code == 0, result.output
    assert result.output.strip() == 'He said "hi"'


def test_json_payload_in_single_quotes_survives_format():
    source = 'payload: str = \'{"ok": true}\';\nsay(payload);\n'
    formatted = _assert_idempotent(source)
    result = run_echo(formatted)
    assert result.exit_code == 0, result.output
    assert result.output.strip() == '{"ok": true}'


def test_interpolation_with_inner_quotes_survives_format():
    source = 'name: str = "Ada";\nsay(\'Hello "${name}"\');\n'
    formatted = _assert_idempotent(source)
    result = run_echo(formatted)
    assert result.exit_code == 0, result.output
    assert result.output.strip() == 'Hello "Ada"'


def test_string_with_both_quote_styles_stays_parseable():
    source = "say('He said \"hi\" and \\'bye\\'');\n"
    formatted = _assert_idempotent(source)
    result = run_echo(source)
    formatted_result = run_echo(formatted)
    assert result.exit_code == 0, result.output
    assert formatted_result.exit_code == 0, formatted_result.output
    assert formatted_result.output == result.output
    assert formatted_result.output.strip() == "He said \"hi\" and 'bye'"
