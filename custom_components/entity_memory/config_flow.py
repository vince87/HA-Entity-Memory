"""Config flow for Entity Memory."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_ATTRIBUTE_CHANGES,
    CONF_IGNORE_UNAVAILABLE,
    CONF_WINDOW_HOURS,
    DEFAULT_ATTRIBUTE_CHANGES,
    DEFAULT_IGNORE_UNAVAILABLE,
    DEFAULT_WINDOW_HOURS,
    DOMAIN,
    MAX_WINDOW_HOURS,
    MIN_WINDOW_HOURS,
)
from .selection import (
    all_entities_config,
    known_entity_ids,
    parse_patterns,
    patterns_are_valid,
)


def _available_entity_ids(hass: HomeAssistant) -> set[str]:
    """Return entities known from both the state machine and registry."""
    return known_entity_ids(hass.states.async_entity_ids(), er.async_get(hass).entities)


def _submitted(user_input: dict[str, Any]) -> dict[str, Any]:
    """Empty exclusions are intentional; never reseed recommendations on save."""
    return {
        **user_input,
        "selection_mode": "all",
        "entities": [],
        "entity_patterns": "*",
        "exclude_patterns": user_input.get("exclude_patterns", ""),
    }


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the shared configuration schema."""
    return vol.Schema(
        {
            vol.Optional(
                "exclude_patterns", default=defaults.get("exclude_patterns", "")
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required(
                CONF_WINDOW_HOURS,
                default=defaults.get(CONF_WINDOW_HOURS, DEFAULT_WINDOW_HOURS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_WINDOW_HOURS,
                    max=MAX_WINDOW_HOURS,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_IGNORE_UNAVAILABLE,
                default=defaults.get(
                    CONF_IGNORE_UNAVAILABLE, DEFAULT_IGNORE_UNAVAILABLE
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_ATTRIBUTE_CHANGES,
                default=defaults.get(CONF_ATTRIBUTE_CHANGES, DEFAULT_ATTRIBUTE_CHANGES),
            ): selector.BooleanSelector(),
        }
    )


class EntityMemoryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle initial configuration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the single Entity Memory entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors: dict[str, str] = {}
        if user_input is not None:
            if not patterns_are_valid(
                parse_patterns(user_input.get("exclude_patterns"))
            ):
                errors["exclude_patterns"] = "invalid_entity_patterns"
            else:
                return self.async_create_entry(
                    title="Entity Memory", data=_submitted(user_input)
                )
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                all_entities_config(
                    {} if user_input is None else _submitted(user_input),
                    _available_entity_ids(self.hass),
                )
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return EntityMemoryOptionsFlow()


class EntityMemoryOptionsFlow(OptionsFlow):
    """Edit Entity Memory configuration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        defaults = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            if not patterns_are_valid(
                parse_patterns(user_input.get("exclude_patterns"))
            ):
                errors["exclude_patterns"] = "invalid_entity_patterns"
            else:
                return self.async_create_entry(data=_submitted(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                all_entities_config(
                    defaults if user_input is None else _submitted(user_input),
                    _available_entity_ids(self.hass),
                )
            ),
            errors=errors,
        )
