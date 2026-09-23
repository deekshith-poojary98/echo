from helpers import run_echo


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
