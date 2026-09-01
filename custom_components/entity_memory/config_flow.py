"""Config flow for Entity Memory."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers import selector

from .const import (
    CONF_ATTRIBUTE_CHANGES,
    CONF_ENTITIES,
    CONF_IGNORE_UNAVAILABLE,
    CONF_WINDOW_HOURS,
    DEFAULT_ATTRIBUTE_CHANGES,
    DEFAULT_IGNORE_UNAVAILABLE,
    DEFAULT_WINDOW_HOURS,
    DOMAIN,
    MAX_ENTITIES,
    MAX_WINDOW_HOURS,
    MIN_WINDOW_HOURS,
    SUPPORTED_DOMAINS,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the shared configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_ENTITIES, default=defaults.get(CONF_ENTITIES, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=list(SUPPORTED_DOMAINS), multiple=True)
            ),
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
                default=defaults.get(CONF_IGNORE_UNAVAILABLE, DEFAULT_IGNORE_UNAVAILABLE),
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

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Create the single Entity Memory entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors: dict[str, str] = {}
        if user_input is not None:
            if len(user_input[CONF_ENTITIES]) > MAX_ENTITIES:
                errors[CONF_ENTITIES] = "too_many_entities"
            else:
                return self.async_create_entry(title="Entity Memory", data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return EntityMemoryOptionsFlow()


class EntityMemoryOptionsFlow(OptionsFlow):
    """Edit Entity Memory configuration."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage options."""
        defaults = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            if len(user_input[CONF_ENTITIES]) > MAX_ENTITIES:
                errors[CONF_ENTITIES] = "too_many_entities"
            else:
                return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=_schema(defaults), errors=errors
        )
