from echo.formatter import format_source


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
}
"""
    formatted = _assert_idempotent(source)
    assert "punct: str = \"!\"" in formatted
    assert "parts: str..." in formatted
    assert "fn(x: int) -> int { return x; }" in formatted
    assert "xs[1:3]" in formatted


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
