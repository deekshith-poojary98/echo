from helpers import assert_no_python_leak, run_echo


def test_clone_class_instance_is_deep():
    result = run_echo(
        """
class Box {
    new {
        items: list;
    }
}

inner: list = [1];
b: Box = Box { items: inner };
c: Box = b.clone();
inner.push(2);
say(c.items);
say(b.items);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1]", "[1, 2]"]


def test_clone_class_preserves_type():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }

    fn sum(this) -> int {
        return this.x + this.y;
    }
}

p: Point = Point(3, 4);
q: Point = p.clone();
q.x = 10;
say(p.sum());
say(q.sum());
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "14"]


def test_clone_deeply_nested_list_is_echo_error_not_python():
    result = run_echo(
        """
xs: list = [];
for i: int in 1..1200 {
    nxt: list = [];
    nxt.push(xs);
    xs = nxt;
}
xs.clone();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "E2609" in result.output
    assert "reached" not in result.lines


def test_clone_deeply_nested_hash_is_echo_error_not_python():
    result = run_echo(
        """
h: hash = {};
for i: int in 1..1200 {
    nxt: hash = {};
    nxt["k"] = h;
    h = nxt;
}
h.clone();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "reached" not in result.lines


def test_clone_deeply_nested_class_instance_is_echo_error_not_python():
    result = run_echo(
        """
class Box {
    new {
        inner: dynamic = null;
    }
}
deep: Box = Box {};
for i: int in 1..1200 {
    nxt: Box = Box {};
    nxt.inner = deep;
    deep = nxt;
}
deep.clone();
say("reached");
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "nested too deeply" in result.output
    assert "reached" not in result.lines
