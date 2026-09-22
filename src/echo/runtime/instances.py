from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassRecord:
    """Identity and members of one class declaration.

    Distinct modules may export different classes with the same name. Dispatch,
    construction defaults, and nominal type checks use this record — never the
    bare name — so a later module cannot steal another class's methods.
    Field-default expressions are evaluated in ``closure``, the environment
    where the class was declared, matching function-default rules.
    """

    name: str
    methods: dict[str, object] = field(default_factory=dict)
    field_defaults: dict[str, object] = field(default_factory=dict)
    field_types: dict[str, object] = field(default_factory=dict)
    method_types: dict[str, object] = field(default_factory=dict)
    class_id: int = 0
    # Defining environment so field defaults close over the class module,
    # matching function-default evaluation (not the construction-site env).
    closure: object | None = None
    private_fields: frozenset[str] = field(default_factory=frozenset)
    private_methods: frozenset[str] = field(default_factory=frozenset)


@dataclass
class ClassInstance:
    class_name: str
    fields: dict[str, object] = field(default_factory=dict)
    record: ClassRecord | None = None
