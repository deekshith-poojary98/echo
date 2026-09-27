from echo.core.yamlutil import parse_yaml
from echo.errors import EchoRuntimeError
from helpers import assert_no_python_leak, run_echo
from modules.harness import assert_echo_error, assert_success, run_entry, write_modules


def test_yaml_parse_write_roundtrip():
    result = run_echo(
        """
data: hash = yamlParse("n: 1\\nok: true\\nxs:\\n  - 2\\n  - hi");
say(data["n"]);
say(data["ok"]);
say(data["xs"][1]);
text: str = yamlWrite({ a: 1, b: "x" });
say(text.contains("a: 1"));
say(text.contains("b: x"));
say("name: Echo".yamlParse()["name"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["1", "true", "hi", "true", "true", "Echo"]


def test_yaml_null_and_scalar():
    result = run_echo(
        """
say(yamlParse("null"));
say(yamlWrite(null));
say(yamlParse("3.5").type());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["null", "null", "float"]


def test_yaml_parse_bad_type():
    result = run_echo("yamlParse(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output
    assert "yamlParse() requires a string" in result.output


def test_yaml_parse_invalid():
    result = run_echo('yamlParse(": [");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output
    assert "Invalid YAML" in result.output


def test_yaml_parse_rejects_alias_cycles_without_python_recursion():
    result = run_echo('yamlParse("a: &anchor\\n  self: *anchor\\n");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output
    assert "cyclic YAML" in result.output


def test_yaml_parse_rejects_list_alias_cycles_without_python_recursion():
    result = run_echo('yamlParse("&a\\n- *a\\n");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output
    assert "cyclic YAML" in result.output


def test_yaml_parse_allows_shared_aliases():
    result = run_echo(
        """
data: hash = yamlParse("x: &a\\n  n: 1\\ny: *a\\n");
say(data["x"]["n"]);
say(data["y"]["n"]);
"""
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["1", "1"]


def test_yaml_parse_or_alias_cycle_returns_fallback():
    result = run_echo('say(yamlParseOr("a: &anchor\\n  self: *anchor\\n", "cycle"));\n')
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert result.lines == ["cycle"]


def test_parse_yaml_direct_alias_cycle_is_echo_error():
    try:
        parse_yaml("a: &anchor\n  self: *anchor\n")
    except RecursionError as exc:
        raise AssertionError("RecursionError leaked from parse_yaml") from exc
    except EchoRuntimeError as exc:
        assert "cyclic YAML" in exc.message
        assert exc.code == "E2855"
        return
    raise AssertionError("parse_yaml accepted cyclic YAML aliases")


def test_yaml_write_unsupported():
    result = run_echo(
        """
fn f() {}
yamlWrite(f);
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output


def test_yaml_parse_or_invalid_returns_fallback():
    result = run_echo('say(yamlParseOr(": [", "bad"));\nsay(": [".yamlParseOr(0));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["bad", "0"]


def test_yaml_parse_or_valid_returns_value():
    result = run_echo(
        """
data: dynamic = yamlParseOr("n: 1", null);
say(data["n"]);
say(yamlParseOr("- true\\n- 2", []).length());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["1", "2"]


def test_yaml_parse_or_non_string_is_type_error():
    result = run_echo("say(yamlParseOr(1, null));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2855" in result.output
    assert "yamlParseOr() requires a string" in result.output


def test_yaml_parse_still_aborts_on_invalid():
    result = run_echo('say(yamlParse(": ["));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Invalid YAML" in result.output


def test_std_yaml_import(tmp_path):
    write_modules(
        tmp_path,
        {
            "app.echo": """
                import yamlParse from "std/yaml";
                import yamlParseOr from "std/yaml";
                import yamlWrite from "std/yaml";
                data: hash = yamlParse("n: 7");
                say(data["n"]);
                say(yamlWrite({ ok: true }));
                say(yamlParseOr(": [", { ok: false })["ok"]);
            """
        },
    )
    assert_success(run_entry(tmp_path), "7\nok: true\nfalse")


def test_std_yaml_require_std(tmp_path):
    from echo.runtime.host import Host

    write_modules(
        tmp_path,
        {
            "app.echo": """
                import yamlParse from "std/yaml";
                say(yamlParse("n: 9")["n"]);
            """
        },
    )
    assert_success(run_entry(tmp_path, host=Host(require_std=True)), "9")

    write_modules(
        tmp_path,
        {
            "bad.echo": """
                say(yamlParse("n: 1")["n"]);
            """
        },
    )
    assert_echo_error(run_entry(tmp_path, "bad.echo", host=Host(require_std=True)), "yamlParse")
