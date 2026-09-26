from helpers import assert_no_python_leak, run_echo


def test_url_encode_decode_roundtrip():
    result = run_echo(
        """
say(urlEncode("a b/c"));
say(urlDecode("a%20b%2Fc"));
say("hello world".urlEncode());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["a%20b%2Fc", "a b/c", "hello%20world"]


def test_url_join():
    result = run_echo(
        """
say(urlJoin("https://example.com/api/", "users"));
say("https://example.com/api/".urlJoin("../v2"));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["https://example.com/api/users", "https://example.com/v2"]


def test_url_query():
    result = run_echo(
        """
q: str = urlQuery({ q: "a b", page: "1" });
say(q);
say({ x: "1" }.urlQuery());
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["q=a+b&page=1", "x=1"]


def test_url_encode_bad_type():
    result = run_echo("urlEncode(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2853" in result.output


def test_url_query_bad_type():
    result = run_echo('urlQuery("nope");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2853" in result.output


def test_url_helpers_with_http_get_shape():
    result = run_echo(
        """
base: str = "https://example.com/search";
path: str = urlJoin(base, "?" + urlQuery({ q: "echo lang" }));
say(path.contains("q=echo"));
say(path.startsWith("https://example.com/search"));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["true", "true"]
