from helpers import assert_no_python_leak, run_echo


def test_url_encode_message_style():
    result = run_echo("urlEncode(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2853" in result.output
    assert "urlEncode() text must be a string" in result.output


def test_url_query_message_style():
    result = run_echo('urlQuery("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2853" in result.output
    assert "urlQuery() params must be a hash" in result.output


def test_days_message_style():
    result = run_echo('days("x");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2851" in result.output
    assert "days() count must be an int" in result.output


def test_http_type_error_still_aborts_or_twin():
    result = run_echo('say(httpGetOr(1, "fallback"));\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2852" in result.output
    assert "httpGetOr() url must be a string" in result.output
