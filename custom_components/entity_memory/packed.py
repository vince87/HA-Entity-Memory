"""Lossless compact payloads; retain query keys without decoding JSON."""

import json
import zlib
from dataclasses import dataclass
from datetime import datetime

from .models import EventConfidence, EventOrigin, MemoryEvent


@dataclass(frozen=True, slots=True)
class PackedEvent:
    timestamp: datetime
    old_state: str | None
    new_state: str
    origin: EventOrigin
    payload: bytes

    @classmethod
    def pack(cls, event: MemoryEvent) -> PackedEvent:
        return cls(
            event.timestamp,
            event.old_state,
            event.new_state,
            event.origin,
            zlib.compress(
                json.dumps(event.as_dict(), separators=(",", ":")).encode(), 1
            ),
        )

    def unpack(self) -> MemoryEvent:
        value = json.loads(zlib.decompress(self.payload))
        value["timestamp"] = self.timestamp
        value["origin"] = self.origin
        value["confidence"] = EventConfidence(value["confidence"])
        return MemoryEvent(**value)
