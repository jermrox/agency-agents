"""TOML configuration loading, with environment expansion for secrets.

Config lives in a checked-in ``sources.toml``; secrets never do. Any string
value may reference an environment variable as ``${VAR_NAME}``, which is
resolved at load time. A referenced-but-unset variable is an error rather
than an empty string, so a missing token fails loudly at startup instead of
silently posting nowhere.
"""

from __future__ import annotations

import logging
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .classify import Thresholds

log = logging.getLogger(__name__)

_ENV_REF = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigError(RuntimeError):
    """Malformed configuration."""


def _expand(value: Any, path: str = "") -> Any:
    """Recursively resolve ``${VAR}`` references in strings."""
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            resolved = os.environ.get(name)
            if resolved is None:
                raise ConfigError(
                    f"{path or 'config'} references ${{{name}}} but that "
                    f"environment variable is not set"
                )
            return resolved

        return _ENV_REF.sub(replace, value)
    if isinstance(value, dict):
        return {k: _expand(v, f"{path}.{k}" if path else k) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v, f"{path}[{i}]") for i, v in enumerate(value)]
    return value


@dataclass(slots=True)
class SourceConfig:
    """One configured source adapter."""

    kind: str
    """Adapter name, e.g. ``greenhouse``. Must exist in the source registry."""

    name: str
    """Label used in the ``source`` field and in run summaries."""

    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PublisherConfig:
    kind: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Config:
    sources: list[SourceConfig] = field(default_factory=list)
    publishers: list[PublisherConfig] = field(default_factory=list)
    thresholds: Thresholds = field(default_factory=Thresholds)
    state_path: Path = Path("state/seen.json")
    output_dir: Path = Path("output")

    archive_path: Path | None = Path("state/corpus.jsonl")
    """Full-fidelity corpus. Set to "" to disable archiving entirely.

    Distinct from ``state_path``: that file only remembers *that* we saw a job,
    while this keeps the whole posting at full text so the analysis layer has
    something to mine and history survives a listing being taken down.
    """

    insights_dir: Path | None = Path("output/insights")
    """Where the digest, dashboard, and insights JSON are written."""

    insights_title: str = "Tactical Human Performance Job Market"

    max_age_days: int = 45
    """Drop postings older than this. Stale listings are worse than none."""

    auto_publish: bool = False
    """When false (the default), *nothing* is published without review.

    Publishing to a public brand site is outward-facing and hard to walk back,
    so the safe mode is the default and turning it on is an explicit choice.
    """

    liveness_check: bool = True
    """Re-fetch every already-published posting and retire the dead ones."""

    liveness_workers: int = 8
    """Concurrent liveness checks."""

    liveness_timeout: int = 20

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
        raw_sources = raw.get("source", [])
        data = _expand({k: v for k, v in raw.items() if k != "source"})

        sources: list[SourceConfig] = []
        for index, entry in enumerate(raw_sources):
            if "kind" not in entry:
                raise ConfigError(f"[[source]] #{index + 1} is missing 'kind'")
            name = entry.get("name") or f"{entry['kind']}:{index + 1}"
            # Sources expand one at a time so that a source marked `optional`
            # can be dropped for a missing credential without taking the whole
            # config with it. That is what lets ONE committed config serve both
            # an operator who has a USAJOBS key and one who does not: without
            # it, adding any credentialed source to sources.keyless.toml would
            # make every keyless run fail at startup. Unset variables stay
            # fatal everywhere else, which is the behaviour that matters --
            # a publisher silently posting nowhere is the bug this guards.
            optional = bool(entry.get("optional", False))
            try:
                entry = _expand(entry, f"source.{name}")
            except ConfigError as exc:
                if not optional:
                    raise
                log.warning("source '%s' disabled: %s", name, exc)
                continue
            options = {
                k: v for k, v in entry.items() if k not in {"kind", "name", "optional"}
            }
            sources.append(SourceConfig(kind=entry["kind"], name=name, options=options))

        publishers: list[PublisherConfig] = []
        for index, entry in enumerate(data.get("publisher", [])):
            if "kind" not in entry:
                raise ConfigError(f"[[publisher]] #{index + 1} is missing 'kind'")
            options = {k: v for k, v in entry.items() if k != "kind"}
            publishers.append(PublisherConfig(kind=entry["kind"], options=options))

        threshold_data = data.get("thresholds", {})
        # Read defaults off an instance: Thresholds uses slots, so class-level
        # attribute access yields a descriptor rather than the default value.
        fallback = Thresholds()
        thresholds = Thresholds(
            publish=float(threshold_data.get("publish", fallback.publish)),
            review=float(threshold_data.get("review", fallback.review)),
            min_domain=float(threshold_data.get("min_domain", fallback.min_domain)),
            min_discipline=float(
                threshold_data.get("min_discipline", fallback.min_discipline)
            ),
        )

        runtime = data.get("runtime", {})

        def optional_path(key: str, default: str) -> Path | None:
            """An empty string switches the feature off; absent means default."""
            raw = runtime.get(key, default)
            return Path(raw) if raw else None

        return cls(
            sources=sources,
            publishers=publishers,
            thresholds=thresholds,
            state_path=Path(runtime.get("state_path", "state/seen.json")),
            output_dir=Path(runtime.get("output_dir", "output")),
            archive_path=optional_path("archive_path", "state/corpus.jsonl"),
            insights_dir=optional_path("insights_dir", "output/insights"),
            insights_title=str(
                runtime.get("insights_title", "Tactical Human Performance Job Market")
            ),
            max_age_days=int(runtime.get("max_age_days", 45)),
            auto_publish=bool(runtime.get("auto_publish", False)),
            liveness_check=bool(runtime.get("liveness_check", True)),
            liveness_workers=int(runtime.get("liveness_workers", 8)),
            liveness_timeout=int(runtime.get("liveness_timeout", 20)),
        )
