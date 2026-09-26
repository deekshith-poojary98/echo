from pathlib import Path

from modules.harness import assert_success, run_entry


REPO = Path(__file__).resolve().parents[2]


def test_std_imports_example() -> None:
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


def test_modules_demo_example() -> None:
    result = run_entry(REPO / "examples" / "modules_demo", "app.echo")
    assert_success(result, "2+3 = 5\n6^2 = 36\nstd ready: true")
