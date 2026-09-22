from helpers import run_echo


def test_priv_field_readable_inside_method():
    result = run_echo(
        """
class Counter {
    new {
        priv n: int = 0;
    }

    fn bump(this) {
        this.n += 1;
        say(this.n);
    }
}

c: Counter = Counter {};
c.bump();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_priv_field_inaccessible_outside():
    result = run_echo(
        """
class Counter {
    new {
        priv n: int = 0;
    }
}

c: Counter = Counter {};
say(c.n);
"""
    )
    assert result.exit_code != 0
    assert "private" in result.output.lower() or "E3215" in result.output


def test_priv_method_callable_inside_only():
    result = run_echo(
        """
class Counter {
    new {
        priv n: int = 0;
    }

    priv fn bump(this) {
        this.n += 1;
    }

    fn tick(this) {
        this.bump();
        say(this.n);
    }
}

c: Counter = Counter {};
c.tick();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_priv_method_inaccessible_outside():
    result = run_echo(
        """
class Counter {
    new {
        n: int = 0;
    }

    priv fn bump(this) {
        this.n += 1;
    }
}

c: Counter = Counter {};
c.bump();
"""
    )
    assert result.exit_code != 0
    assert "private" in result.output.lower() or "E3215" in result.output


def test_priv_method_cannot_satisfy_interface():
    result = run_echo(
        """
interface Named {
    fn name(this) -> str;
}

class User implements Named {
    new {
        label: str;
    }

    priv fn name(this) -> str {
        return this.label;
    }
}
"""
    )
    assert result.exit_code != 0


def test_construction_may_set_priv_fields():
    result = run_echo(
        """
class Point {
    new {
        priv x: int;
        y: int;
    }

    fn sum(this) -> int {
        return this.x + this.y;
    }
}

p: Point = Point { x: 3, y: 4 };
say(p.sum());
say(p.y);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["7", "4"]
