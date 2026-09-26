from pathlib import Path

from helpers import assert_no_python_leak, run_echo
from echo.runtime.host import Host

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_playground_worker_host_policy():
    worker = (REPO_ROOT / "docs" / "public" / "echo-playground-worker.js").read_text(encoding="utf-8")
    assert "Host(allow_files=False, allow_run=False, allow_http=False, environ={})" in worker


def test_playground_docs_describe_host_policy():
    page = (REPO_ROOT / "docs" / "playground.md").read_text(encoding="utf-8")
    assert "allow_http" in page or "HTTP" in page
    assert "E2801" in page
    assert "restricted host" in page.lower() or "No filesystem" in page or "no HTTP" in page.lower()


def test_playground_ui_mentions_policy():
    vue = (REPO_ROOT / "docs" / ".vitepress" / "theme" / "Playground.vue").read_text(encoding="utf-8")
    assert "E2801" in vue
    assert 'id: \'urls\'' in vue or 'id: "urls"' in vue


def test_url_helpers_work_when_http_denied():
    result = run_echo(
        """
say(urlEncode("a b"));
say(httpOk(204));
""",
        host=Host(allow_http=False),
    )
    assert result.exit_code == 0, result.output
    assert result.lines == ["a%20b", "true"]
    assert_no_python_leak(result)


def test_http_get_denied_under_playground_flags():
    result = run_echo(
        'httpGet("https://example.com/");\n',
        host=Host(allow_files=False, allow_run=False, allow_http=False, environ={}),
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2801" in result.output
