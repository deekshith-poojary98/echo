from contextlib import redirect_stdout
from io import StringIO

from echo.cli.main import main
from echo.runtime.host import Host
from helpers import REPO_ROOT, assert_no_python_leak, run_echo
from modules.harness import assert_success, run_entry, write_modules


def test_args_empty_by_default():
    result = run_echo("say(args());\n")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "[]"


def test_args_returns_program_arguments():
    result = run_echo(
        "foreach flag: str in args() { say(flag); }\n",
        host=Host(args=["input.txt", "--verbose"]),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["input.txt", "--verbose"]


def test_args_rejects_extra_arguments():
    result = run_echo("say(args(1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "takes no arguments" in result.output


def test_cli_passes_remainder_after_dash_dash(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("foreach flag: str in args() { say(flag); }\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([str(app), "--plain", "--", "one", "--verbose"])
    assert code == 0
    assert stdout.getvalue().splitlines() == ["one", "--verbose"]


def test_cli_treats_extra_positionals_as_program_args(tmp_path):
    app = tmp_path / "app.echo"
    app.write_text("foreach flag: str in args() { say(flag); }\n", encoding="utf-8")
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([str(app), "--plain", "alpha", "beta"])
    assert code == 0
    assert stdout.getvalue().splitlines() == ["alpha", "beta"]


def test_env_reads_host_map():
    result = run_echo(
        'say(env("CITY"));\n',
        host=Host(environ={"CITY": "Bengaluru"}),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "Bengaluru"


def test_env_empty_string_is_set():
    result = run_echo(
        'say(env("EMPTY") == "");\n',
        host=Host(environ={"EMPTY": ""}),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "true"


def test_env_missing_aborts():
    result = run_echo('say(env("MISSING"));\n', host=Host(environ={}))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not set" in result.output


def test_env_or_fallback():
    result = run_echo(
        'say(envOr("CITY", "unknown"));\nsay(envOr("HOME", "no"));\n',
        host=Host(environ={"HOME": "/tmp"}),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["unknown", "/tmp"]


def test_read_and_write_file(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("hello", encoding="utf-8")
    result = run_echo(
        """
text: str = readFile("notes.txt");
writeFile("out.txt", text + "!");
say(readFile("out.txt"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "hello!"
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "hello!"


def test_read_file_missing_is_echo_error(tmp_path):
    result = run_echo('say(readFile("nope.txt"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "file not found" in result.output


def test_file_denied_on_restricted_host():
    result = run_echo('say(readFile("notes.txt"));\n', host=Host(allow_files=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not available in this host" in result.output


def test_file_exists_true_and_false(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "folder").mkdir()
    result = run_echo(
        """
say(fileExists("notes.txt"));
say(fileExists("missing.txt"));
say(fileExists("folder"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "false"]


def test_file_exists_denied_on_restricted_host():
    result = run_echo('say(fileExists("notes.txt"));\n', host=Host(allow_files=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not available in this host" in result.output


def test_file_exists_rejects_non_string_path():
    result = run_echo("say(fileExists(1));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "path must be a string" in result.output


def test_parse_and_write_json_round_trip():
    result = run_echo(
        """
data: dynamic = parseJson("{\\"n\\": 1, \\"ok\\": true, \\"xs\\": [2]}");
say(data["n"].type());
say(data["ok"]);
say(writeJson(data));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines[0] == "int"
    assert result.lines[1] == "true"
    assert '"n": 1' in result.lines[2]
    assert '"ok": true' in result.lines[2]


def test_parse_json_invalid_is_echo_error():
    result = run_echo('say(parseJson("{"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Invalid JSON" in result.output


def test_parse_json_float_stays_float():
    result = run_echo('say(parseJson("1.5").type());\n')
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "float"


def test_imported_module_sees_same_args(tmp_path):
    write_modules(
        tmp_path,
        {
            "lib.echo": """
                export fn first() -> str {
                    flags: list = args();
                    return flags[0];
                }
            """,
            "app.echo": """
                import first from "lib";
                say(first());
            """,
        },
    )
    result = run_entry(tmp_path, host=Host(args=["shared"]))
    assert_success(result, "shared")


def test_write_json_rejects_non_echo_function():
    result = run_echo(
        """
fn id(x: int) -> int {
    return x;
}
say(writeJson(1));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "1"


def test_json_report_example_summarizes_and_writes(tmp_path):
    source = (REPO_ROOT / "examples" / "json_report.echo").read_text(encoding="utf-8")
    sample = str(REPO_ROOT / "examples" / "sample_jobs.json")
    out = tmp_path / "report.json"
    result = run_echo(
        source,
        filename="json_report.echo",
        host=Host(args=[sample, str(out)]),
    )
    assert result.exit_code == 0, result.output
    assert_no_python_leak(result)
    assert "wrote" in result.output
    report = out.read_text(encoding="utf-8")
    assert '"suite": "checkout"' in report
    assert '"passed": 2' in report
    assert '"failed": 1' in report


def test_cwd_returns_host_directory(tmp_path):
    result = run_echo("say(cwd());\n", host=Host(cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert result.output.strip() == str(tmp_path.resolve())


def test_cwd_rejects_arguments():
    result = run_echo('say(cwd("x"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "takes no arguments" in result.output


def test_exit_stops_with_code_and_keeps_output():
    result = run_echo('say("done");\nexit(2);\nsay("nope");\n')
    assert result.exit_code == 2
    assert_no_python_leak(result)
    assert result.output.strip() == "done"
    assert "Error" not in result.output
    assert "exit(2)" not in result.output


def test_exit_zero_is_success():
    result = run_echo("exit(0);\n")
    assert result.exit_code == 0
    assert result.output == ""


def test_exit_rejects_bool():
    result = run_echo("exit(true);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "must be an integer" in result.output


def test_is_dir_true_and_false(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "folder").mkdir()
    result = run_echo(
        """
say(isDir("folder"));
say(isDir("notes.txt"));
say(isDir("missing"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "false", "false"]


def test_is_dir_denied_on_restricted_host():
    result = run_echo('say(isDir("folder"));\n', host=Host(allow_files=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not available in this host" in result.output


def test_list_files_sorted_names(tmp_path):
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    result = run_echo('say(listFiles("."));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert result.output.strip() == '["a.txt", "b.txt", "sub"]'


def test_list_files_empty_directory(tmp_path):
    result = run_echo('say(listFiles("."));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "[]"


def test_list_files_missing_is_echo_error(tmp_path):
    result = run_echo('say(listFiles("nope"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "directory not found" in result.output


def test_list_files_rejects_file_path(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    result = run_echo('say(listFiles("notes.txt"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not a directory" in result.output


def test_list_files_denied_on_restricted_host():
    result = run_echo('say(listFiles("."));\n', host=Host(allow_files=False))
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "not available in this host" in result.output


def test_exit_from_imported_module(tmp_path):
    write_modules(
        tmp_path,
        {
            "lib.echo": """
                export fn ready() -> bool {
                    return true;
                }
                say("lib");
                exit(3);
            """,
            "app.echo": """
                import ready from "lib";
                say("app");
            """,
        },
    )
    result = run_entry(tmp_path)
    assert result.exit_code == 3
    assert_no_python_leak(result)
    assert result.output.strip() == "lib"
