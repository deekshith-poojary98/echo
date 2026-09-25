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


def test_hash_rest_omits_priv_fields_outside_class():
    result = run_echo(
        """
class Vault {
    new {
        priv secret: str = "s3cret";
        label: str = "public";
    }
}

v: Vault = Vault {};
{ label: str, rest: dynamic... } = v;
say(label);
say(rest.has("secret"));
say(rest.has("label"));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["public", "false", "false"]


def test_named_priv_destructure_is_e3215():
    result = run_echo(
        """
class Vault {
    new {
        priv secret: str = "s3cret";
    }
}

v: Vault = Vault {};
{ secret: str } = v;
say(secret);
"""
    )
    assert result.exit_code != 0
    assert "private" in result.output.lower() or "E3215" in result.output


def test_switch_named_priv_field_is_e3215():
    result = run_echo(
        """
class Vault {
    new {
        priv secret: str = "s3cret";
        label: str = "public";
    }
}

v: Vault = Vault {};
switch v {
    { secret: str } { say(secret); }
    else { say("else"); }
}
"""
    )
    assert result.exit_code != 0
    assert "private" in result.output.lower() or "E3215" in result.output


def test_switch_rest_omits_priv_fields_outside_class():
    result = run_echo(
        """
class Vault {
    new {
        priv secret: str = "s3cret";
        label: str = "public";
    }
}

v: Vault = Vault {};
switch v {
    { label: str, rest: dynamic... } {
        say(label);
        say(rest.has("secret"));
    }
    else { say("else"); }
}
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["public", "false"]


def test_hash_rest_includes_priv_fields_inside_method():
    result = run_echo(
        """
class Vault {
    new {
        priv secret: str = "s3cret";
        label: str = "public";
    }

    fn dump(this) {
        { label: str, rest: dynamic... } = this;
        say(rest["secret"]);
    }
}

v: Vault = Vault {};
v.dump();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "s3cret"
