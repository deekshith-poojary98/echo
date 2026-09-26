from pathlib import Path

from helpers import run_echo_file
from modules.harness import assert_success, run_entry


REPO = Path(__file__).resolve().parents[2]


def test_yaml_and_math_example() -> None:
    result = run_echo_file(REPO / "examples" / "yaml_and_math.echo")
    assert result.exit_code == 0, result.output
    out = result.output
    assert "name: Echo" in out
    assert "score: 3.7" in out
    assert "floor: 3" in out
    assert "abs: 12" in out
    assert "min: 2" in out
    assert "fallback: false" in out
    assert "TRACE: Echo" in out
    assert "traced: Echo" in out
    assert "ok: true" in out


def test_std_imports_still_ok() -> None:
    result = run_entry(REPO / "examples", "std_imports.echo")
    assert_success(
        result,
        "\n".join(
            [
                "std ready: true",
                "std name: echo-std",
                "base64: ZWNobyBsYW5n",
                "roundtrip: echo lang",
                "encoded space: a%20b",
                "query: q=echo+lang&page=1",
                "ok status: true",
                "redirect: true",
            ]
        ),
    )
