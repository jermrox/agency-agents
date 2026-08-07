"""Publisher registry: maps a config ``kind`` to a publisher class."""

from __future__ import annotations

from typing import Any

from .base import Publisher
from .files import FILE_PUBLISHERS
from .webhooks import WEBHOOK_PUBLISHERS

_REGISTRY: dict[str, type[Publisher]] = {
    cls.kind: cls for cls in (*FILE_PUBLISHERS, *WEBHOOK_PUBLISHERS)
}


def available_kinds() -> list[str]:
    return sorted(_REGISTRY)


def build_publisher(kind: str, options: dict[str, Any]) -> Publisher:
    try:
        cls = _REGISTRY[kind]
    except KeyError:
        raise KeyError(
            f"unknown publisher kind '{kind}'. Available: {', '.join(available_kinds())}"
        ) from None
    return cls(options=options)


__all__ = ["Publisher", "available_kinds", "build_publisher"]
