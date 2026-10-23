from helpers import run_echo
from echo.runtime.host import Host


def test_mkdir_all_creates_parents(tmp_path):
    result = run_echo(
        """
mkdirAll("a/b/c");
say(isDir("a/b/c"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0
    assert result.output.strip() == "true"
    assert (tmp_path / "a" / "b" / "c").is_dir()


def test_mkdir_all_existing_directory_is_ok(tmp_path):
    (tmp_path / "out").mkdir()
    result = run_echo('mkdirAll("out");\nsay(isDir("out"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0
    assert result.output.strip() == "true"


def test_mkdir_all_file_in_the_way_aborts(tmp_path):
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    result = run_echo('mkdirAll("notes.txt");\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert "file in the way" in result.output


def test_mkdir_all_method_form(tmp_path):
    result = run_echo('"deep/nested".mkdirAll();\nsay(isDir("deep/nested"));\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 0
    assert result.output.strip() == "true"


def test_mkdir_all_denied_on_restricted_host():
    result = run_echo('mkdirAll("out");\n', host=Host(allow_files=False))
    assert result.exit_code == 1
    assert "not available" in result.output


def test_remove_tree_deletes_directory_tree(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "f.txt").write_text("hi", encoding="utf-8")
    result = run_echo(
        """
removeTree("a");
say(isDir("a"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0
    assert result.output.strip() == "false"
    assert not (tmp_path / "a").exists()


def test_remove_tree_deletes_file(tmp_path):
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    result = run_echo(
        """
removeTree("notes.txt");
say(fileExists("notes.txt"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0
    assert result.output.strip() == "false"


def test_remove_tree_missing_aborts(tmp_path):
    result = run_echo('removeTree("missing");\n', host=Host(cwd=tmp_path))
    assert result.exit_code == 1
    assert "not found" in result.output


def test_remove_tree_denied_on_restricted_host(tmp_path):
    (tmp_path / "out").mkdir()
    result = run_echo('removeTree("out");\n', host=Host(allow_files=False, cwd=tmp_path))
    assert result.exit_code == 1
    assert "not available" in result.output


def test_remove_tree_unlinks_symlink_not_target_tree(tmp_path):
    target = tmp_path / "keepdir"
    target.mkdir()
    (target / "secret.txt").write_text("secret", encoding="utf-8")
    link = tmp_path / "aliasdir"
    link.symlink_to("keepdir")
    result = run_echo(
        """
removeTree("aliasdir");
say(isDir("keepdir"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "true"
    assert target.is_dir()
    assert (target / "secret.txt").read_text(encoding="utf-8") == "secret"
    assert not link.exists()
    assert not link.is_symlink()


def test_remove_tree_unlinks_symlink_to_file(tmp_path):
    real = tmp_path / "notes.txt"
    real.write_text("keep me", encoding="utf-8")
    link = tmp_path / "alias.txt"
    link.symlink_to("notes.txt")
    result = run_echo(
        """
removeTree("alias.txt");
say(fileExists("notes.txt"));
""",
        host=Host(cwd=tmp_path),
    )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "true"
    assert real.is_file()
    assert real.read_text(encoding="utf-8") == "keep me"
    assert not link.is_symlink()
