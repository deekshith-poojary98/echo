from helpers import assert_no_python_leak, run_echo


def test_format_and_parse_time_utc_roundtrip():
    result = run_echo(
        """
stamp: int = parseTime("2020-01-02T03:04:05Z", "%Y-%m-%dT%H:%M:%SZ");
say(stamp);
say(formatTime(stamp, "%Y-%m-%dT%H:%M:%SZ"));
say(formatTime(stamp, "%Y"));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["1577934245", "2020-01-02T03:04:05Z", "2020"]


def test_format_time_method_form():
    result = run_echo('say(0.formatTime("%Y-%m-%d"));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "1970-01-01"


def test_parse_time_method_form():
    result = run_echo('say("1970-01-01".parseTime("%Y-%m-%d"));\n')
    assert result.exit_code == 0
    assert result.output.strip() == "0"


def test_duration_helpers():
    result = run_echo(
        """
say(days(1));
say(hours(2));
say(minutes(3));
say(1.days());
say(now() + hours(1) > now());
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["86400", "7200", "180", "86400", "true"]


def test_parse_time_bad_text_is_e2851():
    result = run_echo('parseTime("nope", "%Y-%m-%d");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2851" in result.output


def test_format_time_bad_type_is_e2851():
    result = run_echo('formatTime("x", "%Y");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2851" in result.output


def test_days_rejects_float():
    result = run_echo("days(1.5);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2851" in result.output
