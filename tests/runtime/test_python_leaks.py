from echo.core.jsonutil import parse_json
from echo.errors import EchoRuntimeError, LexError, ParseError
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.runtime.host import Host
from helpers import assert_no_python_leak, run_echo


def test_foreach_over_int_is_echo_error_not_python():
    result = run_echo(
        """
foreach item: int in 1 {
    say(item);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "foreach" in result.output.lower() or "Type Error" in result.output or "Execution Error" in result.output


def test_foreach_hash_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
foreach k: str in h {
    h["b"] = 2;
    say(k);
}
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["a", "2"]


def test_foreach_hash_take_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1, b: 2 };
foreach k: str in h {
    h.take(k);
    say(k);
}
say(length(h));
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert set(result.lines[:2]) == {"a", "b"}
    assert result.lines[-1] == "0"


def test_foreach_list_push_does_not_hang_or_leak_python():
    result = run_echo(
        """
xs: list = [1, 2];
foreach x: int in xs {
    xs.push(x);
    say(x);
}
say(length(xs));
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["1", "2", "4"]


def test_foreach_list_insert_at_front_does_not_hang_or_leak_python():
    result = run_echo(
        """
xs: list = [1, 2];
foreach x: int in xs {
    xs.insertAt(0, 99);
    say(x);
}
say(xs.asString());
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["1", "2", "[99, 99, 1, 2]"]


def test_map_values_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
fn grow(v: int) -> int {
    use mut h;
    h["b"] = 2;
    return v + 1;
}
say(h.mapValues(grow));
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ['{"a": 2}', "2"]


def test_filter_hash_insert_does_not_leak_python():
    result = run_echo(
        """
h: hash = { a: 1 };
fn keep(v: int) -> bool {
    use mut h;
    h["b"] = 2;
    return true;
}
say(h.filter(keep));
say(h["b"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ['{"a": 1}', "2"]


def test_foreach_over_null_is_echo_error_not_python():
    result = run_echo(
        """
xs: dynamic = null;
foreach item: dynamic in xs {
    say(item);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_order_mixed_types_is_echo_error_not_python():
    result = run_echo(
        """
xs: list = [1, "a"];
xs.order();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_order_mutating_comparator_is_echo_error_not_python():
    # CPython's list.sort raises ValueError when the comparator grows or
    # shrinks the list. CLI / run_source only catch EchoError.
    result = run_echo(
        """
xs: list = [3, 1, 2];
fn cmp(a: int, b: int) -> int {
    use mut xs;
    xs.push(0);
    return a - b;
}
xs.order(cmp);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "order()" in result.output
    assert "while sorting" in result.output
    assert "E2411" in result.output


def test_out_of_range_index_assignment_is_echo_error():
    result = run_echo(
        """
xs: list = [1];
xs[9] = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output.lower() or "Index" in result.output or "Execution Error" in result.output


def test_missing_hash_key_assignment_is_echo_error():
    result = run_echo(
        """
h: hash = {"a": {"b": 1}};
h["missing"]["b"] = 2;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_as_int_invalid_does_not_mention_python_literal():
    result = run_echo('say("abc".asInt());\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_wait_non_numeric_is_echo_error():
    result = run_echo('wait("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output


def test_wait_negative_is_echo_error_not_python():
    result = run_echo("wait(-1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "non-negative" in result.output


def test_wait_nonfinite_is_echo_error_not_python():
    result = run_echo("wait(1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output

    result = run_echo("wait(1e400 - 1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output


def test_wait_integer_too_large_for_float_is_echo_error_not_python():
    huge = "1" + "0" * 400
    result = run_echo(f"wait({huge});\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output


def test_wait_finite_too_large_for_platform_time_is_echo_error_not_python():
    # 1e10 is finite but overflows C time_t; 1e308 is finite float max-ish.
    result = run_echo("wait(1e10);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output

    result = run_echo("wait(1e308);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output

    result = run_echo("wait(10000000000);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "wait()" in result.output
    assert "finite" in result.output


def test_as_int_infinity_is_echo_error_not_python():
    result = run_echo("say(asInt(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_as_int_or_infinity_returns_fallback():
    result = run_echo("say(asIntOr(1e400, 0));\n")
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "0"


def test_as_int_unicode_digit_is_echo_error_not_python():
    result = run_echo('say("²".asInt());\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output

    result = run_echo('say("①".asInt());\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_as_int_or_unicode_digit_returns_fallback():
    result = run_echo('say(asIntOr("²", 0));\n')
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "0"


def test_format_unicode_digit_placeholder_is_echo_error_not_python():
    result = run_echo('say("{²}".format("x"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "placeholder" in result.output.lower() or "format()" in result.output


def test_superscript_number_literal_is_echo_error_not_python():
    result = run_echo("say(²);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)

    result = run_echo("say(1e²);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_as_int_overflowed_multiply_is_echo_error_not_python():
    result = run_echo(
        """
x: float = 1e308;
say(asInt(x * 10));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_floor_ceil_infinity_is_echo_error_not_python():
    result = run_echo("say(floor(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "finite" in result.output.lower() or "floor()" in result.output

    result = run_echo("say(ceil(1e400));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "finite" in result.output.lower() or "ceil()" in result.output


def test_for_and_range_infinity_is_echo_error_not_python():
    result = run_echo(
        """
for i: int in 0...1e400 {
    say(i);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "convertible to int" in result.output

    result = run_echo("say(0...1e400);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "convertible to int" in result.output


def test_for_bool_bound_is_echo_error_not_python_int_true():
    result = run_echo(
        """
for i: int in true..3 {
    say(i);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_remove_missing_value_is_echo_error():
    result = run_echo(
        """
xs: list = [1];
xs.removeValue(9);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not found" in result.output.lower()


def test_hash_take_missing_key_is_echo_error():
    result = run_echo(
        """
h: hash = {};
h.take("nope");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_parse_json_nested_too_deeply_is_echo_error_not_python():
    result = run_echo(
        """
payload: str = "[".repeat(2000) + "]".repeat(2000);
parseJson(payload);
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "reached" not in result.lines


def test_watch_cyclic_class_instance_does_not_leak_python():
    result = run_echo(
        """
class Node {
    new {
        next: dynamic = null;
    }
}
n: Node = Node {};
watch n;
n.next = n;
say("done");
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert "ClassInstance" not in result.output
    assert "WATCH: n modified by field assignment to Node {next: Node {...}} (in global)" in result.output
    assert result.lines[-1] == "done"


def test_watch_deeply_nested_class_instance_does_not_leak_python():
    result = run_echo(
        """
class Box {
    new {
        inner: dynamic = null;
    }
}
deep: Box = Box {};
for i: int in 1..1200 {
    nxt: Box = Box {};
    nxt.inner = deep;
    deep = nxt;
}
n: Box = Box {};
watch n;
n = deep;
say("done");
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert "ClassInstance" not in result.output
    assert "WATCH: n changed to <nested too deeply> (in global)" in result.output
    assert result.lines[-1] == "done"


def test_parse_json_direct_nested_too_deeply_is_echo_error():
    payload = "[" * 2000 + "]" * 2000
    try:
        parse_json(payload)
    except RecursionError as exc:
        raise AssertionError("RecursionError leaked from parse_json") from exc
    except EchoRuntimeError as exc:
        assert "nested too deeply" in exc.message
        assert exc.code == "E2805"
        return
    raise AssertionError("parse_json accepted JSON nested 2000 levels deep")


def test_say_nested_too_deeply_is_echo_error_not_python():
    result = run_echo(
        """
xs: list = [];
for i: int in 1..1200 {
    nxt: list = [];
    nxt.push(xs);
    xs = nxt;
}
say(xs);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output


def test_clone_nested_too_deeply_is_echo_error_not_python():
    result = run_echo(
        """
xs: list = [];
for i: int in 1..1200 {
    nxt: list = [];
    nxt.push(xs);
    xs = nxt;
}
xs.clone();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "reached" not in result.lines


def test_regex_replace_invalid_group_is_echo_error_not_python():
    result = run_echo('say(regexReplace("hello", "(h)", "\\\\2"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex replacement" in result.output


def test_nul_path_is_echo_error_not_python():
    result = run_echo(
        """
path: str = parseJson("\\"foo\\\\u0000bar\\"");
say(readFile(path));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "NUL" in result.output
    assert "E2802" in result.output


def test_nul_path_file_exists_is_echo_error_not_python():
    result = run_echo(
        """
path: str = parseJson("\\"foo\\\\u0000bar\\"");
say(fileExists(path));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "NUL" in result.output


def test_nul_path_write_file_is_echo_error_not_python():
    result = run_echo(
        """
path: str = parseJson("\\"foo\\\\u0000bar\\"");
writeFile(path, "hi");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "NUL" in result.output


def test_nul_run_command_is_echo_error_not_python():
    result = run_echo(
        """
cmd: str = parseJson("\\"echo\\\\u0000x\\"");
say(run(cmd, []));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "NUL" in result.output
    assert "E2822" in result.output


def test_nul_run_arg_is_echo_error_not_python():
    result = run_echo(
        """
arg: str = parseJson("\\"hi\\\\u0000x\\"");
say(run("echo", [arg]));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "NUL" in result.output


def _assert_symlink_loop_is_echo_error(tmp_path, source: str) -> None:
    cycle = tmp_path / "cycle"
    cycle.symlink_to("cycle")
    result = run_echo(source, host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "cycle" in result.output


def test_symlink_loop_file_exists_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'say(fileExists("cycle"));\n')
    result = run_echo('say(fileExists("cycle"));\n', host=Host(cwd=tmp_path))
    assert "invalid path" in result.output or "cannot resolve" in result.output


def test_symlink_loop_is_dir_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'say(isDir("cycle"));\n')


def test_symlink_loop_read_file_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'say(readFile("cycle"));\n')
    result = run_echo('say(readFile("cycle"));\n', host=Host(cwd=tmp_path))
    assert "cannot resolve path" in result.output


def test_symlink_loop_write_file_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'writeFile("cycle", "x");\n')


def test_symlink_loop_list_files_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'say(listFiles("cycle"));\n')


def test_symlink_loop_remove_file_unlinks_the_cycle(tmp_path):
    # A self-referential symlink is a directory entry, not a directory.
    # removeFile must unlink it without following (which would ELOOP).
    cycle = tmp_path / "cycle"
    cycle.symlink_to("cycle")
    result = run_echo('removeFile("cycle");\nsay("ok");\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "ok"
    assert not cycle.is_symlink()
    assert not cycle.exists()


def test_symlink_loop_copy_file_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'copyFile("cycle", "out.txt");\n')


def test_symlink_loop_mkdir_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'mkdir("cycle");\n')


def test_two_node_symlink_loop_is_echo_error_not_python(tmp_path):
    (tmp_path / "a").symlink_to("b")
    (tmp_path / "b").symlink_to("a")
    result = run_echo('say(fileExists("a"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_read_file_or_symlink_loop_returns_fallback(tmp_path):
    (tmp_path / "cycle").symlink_to("cycle")
    result = run_echo('say(readFileOr("cycle", "ok"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "ok"


def test_interpolation_nested_backslash_at_eof_is_echo_error_not_python():
    # File/source with no trailing newline: ${"..." + trailing \\ crashed
    # the lexer with IndexError instead of a syntax diagnostic.
    source = 'say("hello ${"world\\'
    try:
        result = run_echo(source)
    except IndexError as exc:
        raise AssertionError("IndexError leaked from run_echo") from exc
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Unterminated string" in result.output


def test_lexer_interpolation_trailing_backslash_raises_lex_error_not_index_error():
    source = '"hello ${"world\\'
    try:
        Lexer().tokenize(source, filename="<test>")
    except IndexError as exc:
        raise AssertionError("IndexError leaked from Lexer.tokenize") from exc
    except LexError as exc:
        assert "Unterminated string" in exc.message
        return
    raise AssertionError("Lexer.tokenize accepted a nested interpolation string ending in a backslash")


def _nested_interpolation_source(depth: int) -> str:
    inner = "1"
    for _ in range(depth):
        inner = '"${' + inner + '}"'
    return f"say({inner});\n"


def test_deeply_nested_interpolation_is_echo_error_not_python():
    # ~250 nested interpolations recurse through Lexer.tokenize before the
    # parser depth guard can run, leaking RecursionError from run_source.
    result = run_echo(_nested_interpolation_source(300))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E1100" in result.output


def test_lexer_nested_interpolation_raises_lex_error_not_recursion_error():
    source = _nested_interpolation_source(300)
    try:
        Lexer().tokenize(source, filename="<test>")
    except RecursionError as exc:
        raise AssertionError("RecursionError leaked from Lexer.tokenize") from exc
    except LexError as exc:
        assert "nested too deeply" in exc.message
        assert exc.code == "E1100"
        return
    raise AssertionError("Lexer.tokenize accepted 300 levels of nested interpolation")


def test_deeply_nested_parens_is_echo_error_not_python():
    depth = 200
    result = run_echo("(" * depth + "1" + ")" * depth + ";\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E1100" in result.output


def test_deeply_nested_list_literal_is_echo_error_not_python():
    depth = 200
    result = run_echo("say(" + "[" * depth + "]" * depth + ");\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E1100" in result.output


def test_parser_nested_parens_raise_parse_error_not_recursion_error():
    source = "(" * 200 + "1" + ")" * 200 + ";\n"
    try:
        Parser(Lexer().tokenize(source, filename="<test>")).parse()
    except RecursionError as exc:
        raise AssertionError("RecursionError leaked from Parser.parse") from exc
    except ParseError as exc:
        assert "nested too deeply" in exc.message
        assert exc.code == "E1100"
        return
    raise AssertionError("Parser.parse accepted 200 levels of nested parentheses")


def test_unbounded_function_recursion_is_echo_error_not_python():
    result = run_echo(
        """
fn f() {
    f();
}
f();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E2797" in result.output
    assert "reached" not in result.lines


def test_unbounded_method_recursion_is_echo_error_not_python():
    result = run_echo(
        """
class Node {
    fn boom(this) {
        this.boom();
    }
}
n: Node = Node {};
n.boom();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E2797" in result.output
    assert "reached" not in result.lines


def test_equality_nested_too_deeply_is_echo_error_not_python():
    result = run_echo(
        """
left: list = [];
right: list = [];
for i: int in 1..1200 {
    next_left: list = [];
    next_left.push(left);
    left = next_left;
    next_right: list = [];
    next_right.push(right);
    right = next_right;
}
say(left == right);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output


def test_oversized_integer_literal_is_echo_error_not_python():
    result = run_echo("say(" + "1" * 5000 + ");\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E1101" in result.output


def test_oversized_switch_integer_pattern_is_echo_error_not_python():
    result = run_echo("switch " + "1" * 5000 + " { else { say(1); } }\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E1101" in result.output


def test_parser_oversized_integer_raises_parse_error_not_value_error():
    source = "say(" + "1" * 5000 + ");\n"
    try:
        Parser(Lexer().tokenize(source, filename="<test>")).parse()
    except ValueError as exc:
        raise AssertionError("ValueError leaked from Parser.parse") from exc
    except ParseError as exc:
        assert "too large" in exc.message
        assert exc.code == "E1101"
        return
    raise AssertionError("Parser.parse accepted a 5000-digit integer literal")


def test_parse_json_oversized_integer_is_echo_error_not_python():
    result = run_echo('parseJson("' + "1" * 5000 + '");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E2805" in result.output


def test_parse_json_or_oversized_integer_returns_fallback():
    result = run_echo('say(parseJsonOr("' + "1" * 5000 + '", "ok"));\n')
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "ok"


def test_parse_json_direct_oversized_integer_is_echo_error():
    try:
        parse_json("1" * 5000)
    except ValueError as exc:
        raise AssertionError("ValueError leaked from parse_json") from exc
    except EchoRuntimeError as exc:
        assert "too large" in exc.message
        assert exc.code == "E2805"
        return
    raise AssertionError("parse_json accepted a 5000-digit JSON integer")


def test_yaml_parse_oversized_integer_is_echo_error_not_python():
    result = run_echo('yamlParse("' + "1" * 5000 + '");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E2855" in result.output


def test_yaml_parse_or_oversized_integer_returns_fallback():
    result = run_echo('say(yamlParseOr("' + "1" * 5000 + '", "ok"));\n')
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "ok"


def test_say_computed_oversized_integer_is_echo_error_not_python():
    # 4299 nines is under the 4300-digit int() limit; * 100 crosses it.
    result = run_echo(
        """
n: int = "9".repeat(4299).asInt();
say(n * 100);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too many digits" in result.output
    assert "E2806" in result.output


def test_ask_oversized_integer_prompt_is_echo_error_not_python():
    # ask() used str(prompt), so a 4300+ digit integer leaked ValueError.
    result = run_echo(_oversized_int_program("ask(huge);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too many digits" in result.output
    assert "E2806" in result.output


def test_exit_oversized_integer_is_echo_error_not_python():
    # EchoExit formatted the status with f"exit({code})", so a 4300+ digit
    # integer leaked ValueError instead of an Echo diagnostic.
    result = run_echo(_oversized_int_program("exit(huge);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "exit()" in result.output
    assert "too large" in result.output
    assert "E2808" in result.output


def test_exit_status_too_large_for_c_long_is_echo_error_not_python():
    # 2**63 fits in a Python int (19 digits) and used to pass do_exit's
    # str(code) check. CLI `raise SystemExit(code)` then leaked
    # OverflowError: Python int too large to convert to C long.
    result = run_echo("exit(9223372036854775808);\nsay(\"reached\");\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "exit()" in result.output
    assert "too large" in result.output
    assert "E2808" in result.output
    assert "reached" not in result.lines

    result = run_echo("exit(-9223372036854775809);\nsay(\"reached\");\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "reached" not in result.lines


def _oversized_int_program(body: str) -> str:
    return (
        'n: int = "9".repeat(4299).asInt();\n'
        "huge: int = n * 100;\n"
        f"{body}\n"
    )


def test_as_float_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("say(asFloat(huge));"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to float" in result.output
    assert "too many digits" in result.output


def test_list_index_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nsay(xs[huge]);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_list_index_assign_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nxs[huge] = 2;"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_string_index_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program('s: str = "ab";\nsay(s[huge]);'))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_remove_value_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nxs.removeValue(huge);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not found" in result.output.lower()


def test_insert_at_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nxs.insertAt(huge, 2);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_pull_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nxs.pull(huge);"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_slice_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program("xs: list = [1];\nsay(xs.slice(huge, huge));"))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "out of range" in result.output


def test_expect_eq_oversized_integer_is_echo_error_not_python():
    result = run_echo(_oversized_int_program('expectEq(huge, 1, "nope");'))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nope" in result.output
    assert "E2827" in result.output


def test_repeat_count_too_large_for_platform_is_echo_error_not_python():
    # 10**19 exceeds sys.maxsize on 64-bit CPython, so str repeat raises
    # OverflowError instead of attempting the allocation.
    result = run_echo('say("x".repeat(10000000000000000000));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "repeat()" in result.output
    assert "too large" in result.output
    assert "E2816" in result.output

    result = run_echo('say("".repeat(10000000000000000000));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "repeat()" in result.output
    assert "too large" in result.output


def test_repeat_count_too_large_to_allocate_is_echo_error_not_python():
    # sys.maxsize fits in an index-sized integer, so "x" * n raises
    # MemoryError instead of OverflowError. CLI / run_source only catch
    # EchoError, so this used to leak a Python traceback.
    result = run_echo('say("x".repeat(9223372036854775807));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "repeat()" in result.output
    assert "too large" in result.output
    assert "E2816" in result.output


def test_pad_width_too_large_for_platform_is_echo_error_not_python():
    result = run_echo('say("5".padStart(10000000000000000000, "0"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "padStart()" in result.output
    assert "too large" in result.output
    assert "E2817" in result.output

    result = run_echo('say("5".padEnd(10000000000000000000, "0"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "padEnd()" in result.output
    assert "too large" in result.output
    assert "E2817" in result.output


def test_pad_width_too_large_to_allocate_is_echo_error_not_python():
    # sys.maxsize-1 is still index-sized, so building the fill string raises
    # MemoryError instead of OverflowError.
    result = run_echo('say("".padStart(9223372036854775806, "x"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "padStart()" in result.output
    assert "too large" in result.output
    assert "E2817" in result.output

    result = run_echo('say("".padEnd(9223372036854775806, "x"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "padEnd()" in result.output
    assert "too large" in result.output
    assert "E2817" in result.output


def test_range_list_length_too_large_for_platform_is_echo_error_not_python():
    # rangeList materializes every integer. A bound of 10**19 is a valid Echo
    # int but cannot fit in an index-sized list length, so CPython would
    # OverflowError (or the process would grow until OOM) instead of an Echo
    # diagnostic.
    result = run_echo("say(rangeList(0, 10000000000000000000));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "rangeList()" in result.output
    assert "too large" in result.output
    assert "E2843" in result.output

    result = run_echo("say(rangeListInclusive(0, 10000000000000000000));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "rangeListInclusive()" in result.output
    assert "too large" in result.output
    assert "E2843" in result.output


def test_range_expression_length_too_large_for_platform_is_echo_error_not_python():
    result = run_echo("say(0...10000000000000000000);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E2702" in result.output

    result = run_echo("say(0..10000000000000000000);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "too large" in result.output
    assert "E2702" in result.output


def test_oversized_range_with_matching_stride_still_fits():
    # One step the size of the span is a single element, not 10**19 elements.
    result = run_echo("say(0...10000000000000000000 by 10000000000000000000);\n")
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "[0]"

    result = run_echo("say(rangeList(10000000000000000000, 0));\n")
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.output.strip() == "[]"


def test_regex_repetition_too_large_for_platform_is_echo_error_not_python():
    # CPython's re parser raises OverflowError (not re.error) when a `{n}`
    # count exceeds an index-sized integer, so regexMatch leaked a traceback.
    result = run_echo('say(regexMatch("aaa", "a{10000000000000000000}"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex" in result.output
    assert "E2850" in result.output

    result = run_echo('say("aaa".regexMatch("a{1,10000000000000000000}"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex" in result.output
    assert "E2850" in result.output

    result = run_echo('say(regexReplace("aaa", "a{9223372036854775808}", "b"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex" in result.output
    assert "E2850" in result.output

    result = run_echo('say(regexSplit("aaa", "a{10000000000000000000}"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "invalid regex" in result.output
    assert "E2850" in result.output
