"""Integracja Home Assistant dla sterowników kotłów pelletowych Pello v3.5 (esterownik.pl)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ADD_FUEL_MAX,
    ADD_FUEL_MIN,
    ATTR_AMOUNT,
    ATTR_CONFIG_ENTRY_ID,
    DOMAIN,
    SERVICE_ADD_FUEL,
)
from .coordinator import PelloConfigEntry, PelloCoordinator

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ADD_FUEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_AMOUNT): vol.All(
            vol.Coerce(int), vol.Range(min=ADD_FUEL_MIN, max=ADD_FUEL_MAX)
        ),
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Rejestruje akcje integracji."""

    async def _async_add_fuel(call: ServiceCall) -> None:
        entries = [
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
        ]
        if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
            entries = [entry for entry in entries if entry.entry_id == entry_id]
        if len(entries) != 1:
            raise ServiceValidationError(
                "Wskaż config_entry_id sterownika (brak lub więcej niż jeden piec)"
            )
        coordinator: PelloCoordinator = entries[0].runtime_data
        # Zapis ilości paliwa sterownik traktuje jak pełny zasyp i ustawia datę zasypu.
        await coordinator.async_write("add_fuel", str(call.data[ATTR_AMOUNT]))

    hass.services.async_register(DOMAIN, SERVICE_ADD_FUEL, _async_add_fuel, ADD_FUEL_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PelloConfigEntry) -> bool:
    """Uruchamia integrację na podstawie wpisu z UI."""
    coordinator = PelloCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PelloConfigEntry) -> bool:
    """Wyładowuje integrację."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: PelloConfigEntry) -> None:
    """Przeładowuje wpis po zmianie opcji (np. interwału odświeżania)."""
    await hass.config_entries.async_reload(entry.entry_id)
