"""Wspólna klasa bazowa encji Pello."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import UNIQUE_ID_PREFIX
from .coordinator import PelloCoordinator


class PelloEntity(CoordinatorEntity[PelloCoordinator]):
    """Encja powiązana z urządzeniem "Piec Pello 3.5"."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PelloCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{UNIQUE_ID_PREFIX}_{key}"
        self._attr_device_info = coordinator.device_info

    def _raw(self, key: str | None = None) -> str | None:
        """Surowa wartość rejestru albo None, gdy brak lub pusta."""
        data = self.coordinator.data or {}
        value = data.get(key or self._key)
        if value is None or value == "":
            return None
        return value

    def _float(self, key: str | None = None) -> float | None:
        value = self._raw(key)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None
