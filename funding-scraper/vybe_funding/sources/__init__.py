"""Source registry.

Adding an adapter means writing the class and adding one line here. Nothing
else in the pipeline needs to know it exists.
"""

from __future__ import annotations

from typing import Any

from .base import Source, SourceError
from .curated import CuratedSource
from .dod_sbir import DodSbirSource
from .grants_gov import GrantsGovSource
from .sbir_gov import SBIRGovSource

REGISTRY: dict[str, type[Source]] = {
    SBIRGovSource.kind: SBIRGovSource,
    GrantsGovSource.kind: GrantsGovSource,
    DodSbirSource.kind: DodSbirSource,
    CuratedSource.kind: CuratedSource,
}


def build(name: str, options: dict[str, Any]) -> Source:
    """Instantiate the adapter named by ``options['kind']``."""
    kind = options.get("kind")
    if not kind:
        raise SourceError(f"source {name!r} has no `kind`")
    try:
        cls = REGISTRY[kind]
    except KeyError:
        known = ", ".join(sorted(REGISTRY))
        raise SourceError(f"source {name!r} has unknown kind {kind!r} (known: {known})") from None
    return cls(name, options)


__all__ = ["REGISTRY", "build", "Source", "SourceError"]
