"""Nastawy temperatur sterownika Pello."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PelloConfigEntry, PelloCoordinator
from .entity import PelloEntity


@dataclass(frozen=True, kw_only=True)
class PelloNumberDef:
    key: str
    name: str
    minimum: float
    maximum: float
    step: float = 1
    icon: str = "mdi:thermometer-check"
    mode: NumberMode = NumberMode.SLIDER
    category: EntityCategory | None = None


# Zakresy zgodne ze słownikiem rejestrów sterownika (config/hardware.xml).
# Wartości spoza zakresu sterownik i tak odrzuca.
NUMBERS: tuple[PelloNumberDef, ...] = (
    PelloNumberDef(key="cwu_tzad", name="Zadana temperatura CWU", minimum=20, maximum=60),
    PelloNumberDef(key="kot_tzad", name="Zadana temperatura kotła CO", minimum=42, maximum=80),
    PelloNumberDef(
        key="ob1_tzad",
        name="Zadana temperatura za zaworem",
        minimum=20,
        maximum=80,
        icon="mdi:pipe-valve",
    ),
    PelloNumberDef(
        key="ob1_pok_lo",
        name="Temperatura pokojowa niska",
        minimum=5,
        maximum=35,
        step=0.1,
        icon="mdi:home-thermometer-outline",
        mode=NumberMode.BOX,
        category=EntityCategory.CONFIG,
    ),
    PelloNumberDef(
        key="ob1_pok_norm",
        name="Temperatura pokojowa normalna",
        minimum=5,
        maximum=35,
        step=0.1,
        icon="mdi:home-thermometer",
        mode=NumberMode.BOX,
        category=EntityCategory.CONFIG,
    ),
    PelloNumberDef(
        key="ob1_pok_hi",
        name="Temperatura pokojowa komfortowa",
        minimum=5,
        maximum=35,
        step=0.1,
        icon="mdi:home-thermometer",
        mode=NumberMode.BOX,
        category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PelloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PelloNumber(coordinator, definition) for definition in NUMBERS)


class PelloNumber(PelloEntity, NumberEntity):
    """Nastawa temperatury zapisywana przez setregister.cgi."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: PelloCoordinator, definition: PelloNumberDef) -> None:
        super().__init__(coordinator, definition.key, definition.name)
        self._def = definition
        self._attr_native_min_value = definition.minimum
        self._attr_native_max_value = definition.maximum
        self._attr_native_step = definition.step
        self._attr_mode = definition.mode
        self._attr_icon = definition.icon
        self._attr_entity_category = definition.category

    @property
    def native_value(self) -> float | None:
        return self._float()

    async def async_set_native_value(self, value: float) -> None:
        if self._def.step >= 1:
            text = str(int(round(value)))
        else:
            text = f"{value:.1f}"
        await self.coordinator.async_write(self._key, text)
