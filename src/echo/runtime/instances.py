from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassInstance:
    class_name: str
    fields: dict[str, object] = field(default_factory=dict)
