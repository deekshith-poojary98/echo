from echo.cli.main import main
from echo.ide.runner import run_source


def test_ide_help_exits_zero():
    try:
        main(["ide", "-h"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("expected SystemExit from -h")


def test_run_source_captures_say():
    result = run_source('say("hi");')
    assert result.exit_code == 0
    assert "hi" in result.output


def test_run_source_captures_error():
    result = run_source("say(noSuchName);")
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.strip() != ""


def test_run_source_unbounded_recursion_is_echo_error():
    result = run_source(
        """
fn f() {
    f();
}
f();
"""
    )
    assert result.exit_code == 1
    assert "nested too deeply" in result.stderr
    assert "E2797" in result.stderr
    assert "RecursionError" not in result.output
