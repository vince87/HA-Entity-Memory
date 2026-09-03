"""Resolve compact entity-selection rules."""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatchcase

from .const import SUPPORTED_DOMAINS


def known_entity_ids(
    state_entity_ids: Iterable[str], registry_entity_ids: Iterable[str]
) -> set[str]:
    """Combine entity IDs available from Home Assistant's two sources."""
    return set(state_entity_ids) | set(registry_entity_ids)


def parse_patterns(value: str | None) -> list[str]:
    """Return normalized patterns entered one per line or comma separated."""
    if not value:
        return []
    return [
        item.strip().lower()
        for line in value.splitlines()
        for item in line.split(",")
        if item.strip()
    ]


def patterns_are_valid(patterns: Iterable[str]) -> bool:
    """Return whether every pattern targets a supported entity domain."""
    return all(
        "." in pattern
        and pattern.partition(".")[0] in SUPPORTED_DOMAINS
        and " " not in pattern
        for pattern in patterns
    )


def resolve_entities(
    explicit: Iterable[str], patterns: Iterable[str], available: Iterable[str]
) -> set[str]:
    """Combine explicit entities with wildcard matches from known HA entities."""
    resolved = set(explicit)
    candidates = {
        entity_id
        for entity_id in available
        if entity_id.partition(".")[0] in SUPPORTED_DOMAINS
    }
    for pattern in patterns:
        resolved.update(
            entity_id for entity_id in candidates if fnmatchcase(entity_id, pattern)
        )
    return resolved
