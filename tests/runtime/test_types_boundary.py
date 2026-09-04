from helpers import assert_no_python_leak, run_echo


def test_true_is_not_equal_to_one():
    result = run_echo("say(true == 1);\nsay(false == 0);\n")
    assert result.exit_code == 0
    assert result.lines == ["false", "false"]


def test_null_equals_null_and_not_zero():
    result = run_echo("say(null == null);\nsay(null == 0);\n")
    assert result.exit_code == 0
    assert result.lines == ["true", "false"]


def test_lists_and_hashes_compare_structurally():
    result = run_echo(
        """
say([1, 2] == [1, 2]);
say({"a": 1} == {"a": 1});
say([1] == [2]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "true", "false"]


def test_bool_cannot_be_used_as_int_in_arithmetic():
    result = run_echo("say(true + 1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_bool_cannot_be_assigned_to_int():
    result = run_echo("x: int = true;\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_foreach_rejects_bool_items_for_int_variable():
    result = run_echo(
        """
foreach n: int in [true] {
    say(n);
}
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_mixed_str_plus_int_is_type_error():
    result = run_echo('say("a" + 1);\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_string_repeat_is_not_python_repeat():
    result = run_echo('say("a" * 3);\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_list_repeat_is_not_python_repeat():
    result = run_echo("say([1] * 2);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_null_is_not_indexable():
    result = run_echo("x: dynamic = null;\nsay(x[0]);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot index" in result.output


def test_list_index_rejects_bool():
    result = run_echo("xs: list = [1];\nsay(xs[true]);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_hash_index_rejects_int_key():
    result = run_echo('h: hash = {"a": 1};\nsay(h[1]);\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_unknown_type_name_is_an_error():
    result = run_echo("x: Nope = 1;\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Unknown type" in result.output


def test_void_is_not_a_variable_type():
    result = run_echo("x: void = null;\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)


def test_dynamic_accepts_null_and_later_int():
    result = run_echo(
        """
x: dynamic = null;
say(x);
x = 3;
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "3"]


def test_type_alias_is_not_a_new_runtime_type():
    result = run_echo(
        """
type Age = int;
years: Age = 9;
say(type(years));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "int"


def test_object_alias_requires_listed_fields_and_allows_extras():
    result = run_echo(
        """
type User = { id: int, name: str };
ok: User = { id: 1, name: "Ada", extra: true };
say(ok["name"]);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ada"


def test_object_alias_rejects_missing_field():
    result = run_echo(
        """
type User = { id: int, name: str };
bad: User = { id: 1 };
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_argument_type_check_rejects_bool_for_int():
    result = run_echo(
        """
fn id(n: int) -> int { return n; }
say(id(true));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_return_type_check_rejects_bool_for_int():
    result = run_echo(
        """
fn lie() -> int { return true; }
lie();
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Type Error" in result.output


def test_default_uses_truthiness():
    result = run_echo(
        """
say(default(0, 9));
say(default(3, 9));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["9", "3"]


def test_truthiness_table():
    result = run_echo(
        """
fn show(v: dynamic) {
    if v { say("t"); } else { say("f"); }
}
show(false);
show(null);
show(0);
show(0.0);
show("");
show([]);
show({});
show(1);
show("x");
show([0]);
show({"a": 1});
show(true);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["f", "f", "f", "f", "f", "f", "f", "t", "t", "t", "t", "t"]
