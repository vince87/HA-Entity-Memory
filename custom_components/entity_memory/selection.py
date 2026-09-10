"""Resolve compact entity-selection rules."""

from __future__ import annotations

import re
from collections.abc import Iterable
from fnmatch import fnmatchcase


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
    """Accept all domains while preserving existing fnmatch pattern syntax."""
    return all(
        pattern == "*"
        or (
            "." in pattern
            and (
                pattern.partition(".")[0] == "*"
                or re.fullmatch(r"[a-z_]+", pattern.partition(".")[0])
            )
            and " " not in pattern
        )
        for pattern in patterns
    )


def resolve_entities(
    explicit: Iterable[str], patterns: Iterable[str], available: Iterable[str]
) -> set[str]:
    """Combine explicit entities with wildcard matches from known HA entities."""
    resolved = set(explicit)
    candidates = {entity_id for entity_id in available if "." in entity_id}
    for pattern in patterns:
        resolved.update(
            entity_id for entity_id in candidates if fnmatchcase(entity_id, pattern)
        )
    return resolved


def selected(
    entity_id: str, explicit: set[str], patterns: list[str], excludes: list[str]
) -> bool:
    """Match live entities, including entities created after setup."""
    return (
        entity_id in explicit or any(fnmatchcase(entity_id, p) for p in patterns)
    ) and not any(fnmatchcase(entity_id, p) for p in excludes)
