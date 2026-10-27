"""Konfiguracja integracji Pello z poziomu UI."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    PATH_VALUES,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=3600))

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default="root"): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_VALIDATOR,
    }
)


async def _test_connection(hass, host: str, username: str, password: str) -> str | None:
    """Zwraca kod błędu albo None, gdy sterownik odpowiada poprawnie."""
    auth = aiohttp.BasicAuth(username, password or "") if username else None
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"http://{host}/{PATH_VALUES}",
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as response:
            if response.status in (401, 403):
                return "invalid_auth"
            if response.status != 200:
                return "cannot_connect"
            text = await response.text(errors="replace")
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        _LOGGER.debug("Pello: test połączenia nieudany: %s", err)
        return "cannot_connect"
    if "tkot_value" not in text:
        return "not_pello"
    return None


class PelloConfigFlow(ConfigFlow, domain=DOMAIN):
    """Dodawanie sterownika Pello."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            self._async_abort_entries_match({CONF_HOST: host})

            error = await _test_connection(
                self.hass,
                host,
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
            )
            if error is None:
                return self.async_create_entry(
                    title=f"Piec Pello ({host})",
                    data={**user_input, CONF_HOST: host},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await _test_connection(
                self.hass,
                entry.data[CONF_HOST],
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
            )
            if error is None:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME, default=entry.data.get(CONF_USERNAME, "root")
                    ): str,
                    vol.Optional(CONF_PASSWORD, default=""): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PelloOptionsFlow:
        return PelloOptionsFlow()


class PelloOptionsFlow(OptionsFlow):
    """Opcje: interwał odświeżania."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_SCAN_INTERVAL, default=current): SCAN_INTERVAL_VALIDATOR}
            ),
        )
