from echo.formatter import format_source
from echo.runtime.host import Host
from helpers import assert_no_python_leak, run_echo


def test_assign_say_and_call_through_alias():
    result = run_echo(
        """
print: fn(str) -> dynamic = say;
print("hi");
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "hi"


def test_direct_say_call_still_works():
    result = run_echo('say("x");\n')
    assert result.exit_code == 0
    assert result.output.strip() == "x"


def test_pass_map_as_callback_argument():
    result = run_echo(
        """
fn apply(transform: fn(list, fn(int) -> int) -> list, xs: list, f: fn(int) -> int) -> list {
    return transform(xs, f);
}
fn double(x: int) -> int {
    return x * 2;
}
say(apply(map, [1, 2, 3], double));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[2, 4, 6]"


def test_store_builtin_in_list_and_hash():
    result = run_echo(
        """
ops: list = [say];
ops[0]("listed");
named: hash = { out: say };
named["out"]("hashed");
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["listed", "hashed"]


def test_type_of_builtin_value_is_fn():
    result = run_echo(
        """
say(type(say));
say(type(map));
print: fn(str) -> dynamic = say;
say(type(print));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["fn", "fn", "fn"]


def test_map_assigned_to_matching_function_type():
    result = run_echo(
        """
apply: fn(list, fn(int) -> int) -> list = map;
fn inc(x: int) -> int {
    return x + 1;
}
say(apply([1, 2], inc));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[2, 3]"


def test_abs_as_map_callback():
    result = run_echo("say(map([-1, 2, -3], abs));\n")
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]"


def test_return_builtin_from_user_function():
    result = run_echo(
        """
fn printer() -> fn(str) -> dynamic {
    return say;
}
out: fn(str) -> dynamic = printer();
out("returned");
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "returned"


def test_builtin_equality_is_same_name():
    result = run_echo(
        """
print: fn(str) -> dynamic = say;
say(print == say);
say(say == map);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "false"]


def test_const_builtin_binding_cannot_reassign():
    result = run_echo(
        """
const print: fn(str) -> dynamic = say;
print = map;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E3201" in result.output


def test_stringify_builtin_value():
    result = run_echo("say(say);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "<fn say>"


def test_bound_method_is_a_value():
    result = run_echo(
        """
xs: list = [1, 2, 3];
fn double(x: int) -> int {
    return x * 2;
}
mapper: fn(fn(int) -> int) -> list = xs.map;
say(mapper(double));
say(type(xs.map));
say(xs.map(double));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 4, 6]", "fn", "[2, 4, 6]"]


def test_unknown_property_still_errors():
    result = run_echo("xs: list = []; say(xs.nope);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2704" in result.output


def test_host_denied_builtin_is_still_a_value():
    result = run_echo(
        """
reader: dynamic = readFile;
say(type(reader));
reader("notes.txt");
""",
        host=Host(allow_files=False),
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "fn" in result.lines
    assert "E2801" in result.output


def test_variadic_builtin_type_is_documented_shape():
    result = run_echo(
        """
out: fn(dynamic...) -> void = say;
out("a", "b");
joined: fn(dynamic...) -> str = pathJoin;
say(joined("a", "b", "c"));
"""
    )
    assert result.exit_code == 0
    assert result.lines[0] == "a b"
    assert "a" in result.lines[1] and "b" in result.lines[1]


def test_abs_assigned_to_int_function_type():
    result = run_echo(
        """
magnitude: fn(int) -> int = abs;
say(magnitude(-4));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "4"


def test_map_not_assignable_to_wrong_arity():
    result = run_echo("wrong: fn(int) -> int = map;\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output


def test_call_uses_parameter_that_shadows_builtin():
    result = run_echo(
        """
fn ident(xs: list, f: fn(int) -> int) -> list {
    return xs;
}
fn apply(map: fn(list, fn(int) -> int) -> list, xs: list, f: fn(int) -> int) -> list {
    return map(xs, f);
}
fn double(x: int) -> int {
    return x * 2;
}
say(apply(ident, [1, 2, 3], double));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]"


def test_call_uses_variable_that_shadows_builtin():
    result = run_echo(
        """
fn ident(xs: list, f: fn(int) -> int) -> list {
    return xs;
}
map: fn(list, fn(int) -> int) -> list = ident;
fn double(x: int) -> int {
    return x * 2;
}
say(map([1, 2], double));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2]"


def test_formatter_keeps_builtin_as_value():
    source = "print: fn(str) -> dynamic = say;\n"
    assert "say" in format_source(source)
