from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassRecord:
    """Identity and members of one class declaration.

    Distinct modules may export different classes with the same name. Dispatch,
    construction defaults, and nominal type checks use this record — never the
    bare name — so a later module cannot steal another class's methods.
    """

    name: str
    methods: dict[str, object] = field(default_factory=dict)
    field_defaults: dict[str, object] = field(default_factory=dict)
    field_types: dict[str, object] = field(default_factory=dict)
    method_types: dict[str, object] = field(default_factory=dict)
    class_id: int = 0


@dataclass
class ClassInstance:
    class_name: str
    fields: dict[str, object] = field(default_factory=dict)
    record: ClassRecord | None = None
