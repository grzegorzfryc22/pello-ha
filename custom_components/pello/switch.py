"""Przełączniki ustawień sterownika Pello."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PelloConfigEntry, PelloCoordinator
from .entity import PelloEntity

SWITCHES: tuple[tuple[str, str], ...] = (
    ("pog_en", "Regulator pogodowy kotła"),
    ("ob1_pog_en", "Regulator pogodowy obiegu za zaworem"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PelloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PelloSwitch(coordinator, key, name) for key, name in SWITCHES)


class PelloSwitch(PelloEntity, SwitchEntity):
    """Rejestr 0/1 sterownika."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:weather-partly-snowy"

    def __init__(self, coordinator: PelloCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, name)

    @property
    def is_on(self) -> bool | None:
        raw = self._raw()
        return None if raw is None else raw == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self._key, "1")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self._key, "0")
