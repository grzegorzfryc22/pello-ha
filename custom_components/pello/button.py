"""Przyciski poleceń sterownika Pello."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PelloConfigEntry
from .entity import PelloEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PelloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([PelloAckAlarmButton(coordinator, "cmd_ackalarm", "Kasuj alarmy")])


class PelloAckAlarmButton(PelloEntity, ButtonEntity):
    """Potwierdza (kasuje) aktywne alarmy sterownika."""

    _attr_icon = "mdi:alarm-light-off"

    async def async_press(self) -> None:
        await self.coordinator.async_write(self._key, "1")
