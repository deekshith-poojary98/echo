from echo.runtime.host import Host
from helpers import assert_no_python_leak, run_echo


def test_read_file_or_missing_returns_fallback(tmp_path):
    result = run_echo(
        'say(readFileOr("nope.txt", "missing"));\n',
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "missing"


def test_read_file_or_existing_returns_contents(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    result = run_echo(
        'say(readFileOr("notes.txt", "missing"));\nsay("notes.txt".readFileOr("missing"));\n',
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["hello", "hello"]


def test_read_file_or_directory_returns_fallback(tmp_path):
    (tmp_path / "folder").mkdir()
    result = run_echo(
        'say(readFileOr("folder", "not-a-file"));\n',
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "not-a-file"


def test_read_file_or_invalid_utf8_returns_fallback(tmp_path):
    (tmp_path / "bad.txt").write_bytes(b"\xff\xfe")
    result = run_echo(
        'say(readFileOr("bad.txt", "binary"));\n',
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "binary"


def test_read_file_or_denied_host_aborts():
    result = run_echo(
        'say(readFileOr("notes.txt", "fallback"));\n',
        host=Host(allow_files=False),
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not available in this host" in result.output


def test_read_file_or_non_string_path_is_type_error():
    result = run_echo("say(readFileOr(1, \"fallback\"));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "path must be a string" in result.output


def test_read_file_still_aborts_on_missing(tmp_path):
    result = run_echo('say(readFile("nope.txt"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "file not found" in result.output


def test_parse_json_or_invalid_returns_fallback():
    result = run_echo('say(parseJsonOr("{", "bad"));\nsay("{".parseJsonOr(0));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["bad", "0"]


def test_parse_json_or_valid_returns_value():
    result = run_echo(
        """
data: dynamic = parseJsonOr("{\\"n\\": 1}", null);
say(data["n"]);
say(parseJsonOr("[true, 2]", []).length());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["1", "2"]


def test_parse_json_or_non_string_is_type_error():
    result = run_echo("say(parseJsonOr(1, null));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "requires a string" in result.output


def test_parse_json_still_aborts_on_invalid():
    result = run_echo('say(parseJson("{"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Invalid JSON" in result.output


def test_as_int_or_unparseable_string_returns_fallback():
    result = run_echo('say(asIntOr("abc", 0));\nsay("abc".asIntOr(0));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["0", "0"]


def test_as_int_or_parses_trimmed_integer_text():
    result = run_echo('say(asIntOr(" 42 ", 0));\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "42"


def test_as_int_or_bool_is_type_error():
    result = run_echo("say(asIntOr(true, 0));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to int" in result.output


def test_as_int_or_false_is_type_error():
    result = run_echo("say(false.asIntOr(0));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to int" in result.output


def test_as_int_or_null_list_hash_return_fallback():
    result = run_echo(
        """
say(asIntOr(null, 0));
say(asIntOr([1], 0));
say(asIntOr({"n": 1}, 0));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["0", "0", "0"]


def test_as_int_still_aborts_on_unparseable():
    result = run_echo('say(asInt("abc"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert value to int" in result.output


def test_as_float_or_unparseable_string_returns_fallback():
    result = run_echo('say(asFloatOr("abc", 0.0));\nsay("abc".asFloatOr(0.0));\n')
    assert result.exit_code == 0, result.output
    assert result.lines == ["0.0", "0.0"]


def test_as_float_or_parses_trimmed_float_text():
    result = run_echo('say(asFloatOr(" 3.5 ", 0.0));\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "3.5"


def test_as_float_or_bool_is_type_error():
    result = run_echo("say(asFloatOr(true, 0.0));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to float" in result.output


def test_as_float_or_null_list_hash_return_fallback():
    result = run_echo(
        """
say(asFloatOr(null, 0.0));
say(asFloatOr([], 0.0));
say(asFloatOr({}, 0.0));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["0.0", "0.0", "0.0"]


def test_as_float_still_aborts_on_bool():
    result = run_echo("say(asFloat(true));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Cannot convert bool to float" in result.output
