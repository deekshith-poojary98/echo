from helpers import assert_no_python_leak, run_echo


def test_base64_encode_decode_roundtrip():
    result = run_echo(
        """
say(base64Encode("hello"));
say(base64Decode("aGVsbG8="));
say("echo".base64Encode());
say(base64Decode("echo".base64Encode()));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["aGVsbG8=", "hello", "ZWNobw==", "echo"]


def test_base64_unicode_roundtrip():
    result = run_echo(
        """
text: str = "café";
say(base64Decode(base64Encode(text)));
"""
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["café"]


def test_base64_encode_bad_type():
    result = run_echo("base64Encode(1);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2854" in result.output
    assert "base64Encode() text must be a string" in result.output


def test_base64_decode_invalid():
    result = run_echo('base64Decode("!!!!");\n')
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2854" in result.output
    assert "cannot decode base64" in result.output
