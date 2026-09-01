"""Constants for Entity Memory."""

from typing import Final

DOMAIN: Final = "entity_memory"

CONF_ENTITIES: Final = "entities"
CONF_WINDOW_HOURS: Final = "window_hours"
CONF_IGNORE_UNAVAILABLE: Final = "ignore_unavailable"
CONF_ATTRIBUTE_CHANGES: Final = "attribute_changes"

DEFAULT_WINDOW_HOURS: Final = 12
DEFAULT_IGNORE_UNAVAILABLE: Final = True
DEFAULT_ATTRIBUTE_CHANGES: Final = True
MAX_ENTITIES: Final = 50
MAX_WINDOW_HOURS: Final = 240
MIN_WINDOW_HOURS: Final = 1

SUPPORTED_DOMAINS: Final = {
    "binary_sensor",
    "climate",
    "cover",
    "light",
    "switch",
}
IGNORED_STATES: Final = {"unknown", "unavailable"}
SIGNIFICANT_ATTRIBUTES: Final = {
    "climate": frozenset(
        {"hvac_mode", "temperature", "target_temp_high", "target_temp_low", "preset_mode"}
    ),
    "cover": frozenset({"current_position", "current_tilt_position"}),
    "light": frozenset({"brightness", "color_temp_kelvin", "rgb_color", "effect"}),
}
