from echo.core.jsonutil import parse_json
from echo.errors import EchoRuntimeError
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


def test_symlink_loop_remove_file_is_echo_error_not_python(tmp_path):
    _assert_symlink_loop_is_echo_error(tmp_path, 'removeFile("cycle");\n')


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
