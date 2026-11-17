"""Config flow for Meta Muse Image."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CHAT_MODELS,
    CONF_CONTROL_HA,
    CONF_DEFAULT_SIZE,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_OUTPUT_DIR,
    CONF_PROMPT,
    DEFAULT_CHAT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIZE,
    DEFAULT_SYSTEM_PROMPT,
    DOMAIN,
)


class MuseImageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meta Muse Image."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "MuseImageOptionsFlow":
        """Return the options flow so the cogwheel appears for this entry."""
        return MuseImageOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (UI) step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(
                title="Meta Muse",
                data={CONF_API_KEY: user_input[CONF_API_KEY]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): cv.string,
                }
            ),
        )

    async def async_step_import(
        self, import_info: dict[str, Any]
    ) -> ConfigFlowResult:
        """Import a config entry from configuration.yaml."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        options = {
            CONF_OUTPUT_DIR: import_info.get(CONF_OUTPUT_DIR, DEFAULT_OUTPUT_DIR),
            CONF_DEFAULT_SIZE: import_info.get(CONF_DEFAULT_SIZE, DEFAULT_SIZE),
            CONF_LANGUAGE: import_info.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            CONF_MODEL: import_info.get(CONF_MODEL, DEFAULT_CHAT_MODEL),
            CONF_CONTROL_HA: import_info.get(CONF_CONTROL_HA, True),
            CONF_PROMPT: import_info.get(CONF_PROMPT, DEFAULT_SYSTEM_PROMPT),
        }
        return self.async_create_entry(
            title="Meta Muse",
            data={CONF_API_KEY: import_info[CONF_API_KEY]},
            options=options,
        )


class MuseImageOptionsFlow(OptionsFlow):
    """Handle options for Meta Muse Image."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_SIZE,
                        default=options.get(CONF_DEFAULT_SIZE, DEFAULT_SIZE),
                    ): cv.string,
                    vol.Optional(
                        CONF_OUTPUT_DIR,
                        default=options.get(CONF_OUTPUT_DIR, DEFAULT_OUTPUT_DIR),
                    ): cv.string,
                    vol.Optional(
                        CONF_LANGUAGE,
                        default=options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    ): cv.string,
                    vol.Optional(
                        CONF_MODEL,
                        default=options.get(CONF_MODEL, DEFAULT_CHAT_MODEL),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=CHAT_MODELS,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_CONTROL_HA,
                        default=options.get(CONF_CONTROL_HA, True),
                    ): cv.boolean,
                    vol.Optional(
                        CONF_PROMPT,
                        default=options.get(CONF_PROMPT, DEFAULT_SYSTEM_PROMPT),
                    ): TextSelector(
                        TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
                    ),
                }
            ),
        )
