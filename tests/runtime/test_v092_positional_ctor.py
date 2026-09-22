from helpers import run_echo


def test_positional_construction_maps_fields_in_order():
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
say(p.sum());
say(p.x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "3"]


def test_positional_construction_omits_trailing_defaults():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int = 0;
    }
}

p: Point = Point(5);
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["5", "0"]


def test_positional_construction_all_defaults():
    result = run_echo(
        """
class Counter {
    new {
        n: int = 0;
    }
}

c: Counter = Counter();
say(c.n);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "0"


def test_positional_construction_missing_required_is_error():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }
}

p: Point = Point(1);
"""
    )
    assert result.exit_code != 0


def test_positional_construction_rejects_kwargs():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }
}

p: Point = Point(x: 1, y: 2);
"""
    )
    assert result.exit_code != 0


def test_named_construction_still_works():
    result = run_echo(
        """
class Point {
    new {
        x: int;
        y: int;
    }
}

p: Point = Point { y: 4, x: 3 };
say(p.x);
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["3", "4"]
