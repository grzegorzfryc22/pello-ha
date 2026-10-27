"""Tryby pracy sterownika Pello."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import UNIQUE_ID_PREFIX
from .coordinator import PelloConfigEntry, PelloCoordinator
from .entity import PelloEntity


@dataclass(frozen=True, kw_only=True)
class PelloSelectDef:
    key: str  # rejestr zapisywany przez setregister.cgi
    name: str
    options: dict[str, str]  # wartość rejestru -> etykieta
    state_key: str | None = None  # rejestr ze stanem, gdy inny niż zapisywany
    unique_suffix: str | None = None
    icon: str | None = None
    enabled: bool = True


SELECTS: tuple[PelloSelectDef, ...] = (
    PelloSelectDef(
        key="zima_lato",
        name="Tryb pracy (Zima / Lato)",
        options={"0": "Zima", "1": "Lato", "2": "Auto-lato"},
        # Zachowany unique_id z wersji 1.0.x.
        unique_suffix="tryb_zima_lato",
        icon="mdi:theme-light-dark",
    ),
    PelloSelectDef(
        key="cwu_state",
        name="Tryb CWU",
        options={
            "0": "Wyłączona",
            "1": "Harmonogram",
            "2": "Włączona",
            "3": "+1 godzina",
            "4": "+2 godziny",
        },
        icon="mdi:water-boiler",
    ),
    # UWAGA: tryb ręczny zatrzymuje palnik i całe sterowanie (pompy, zawór, podajnik).
    # Dlatego encja jest domyślnie wyłączona — trzeba ją świadomie włączyć.
    PelloSelectDef(
        key="tryb_auto",
        name="Tryb sterowania (Automatyczny / Ręczny)",
        options={"1": "Automatyczny", "0": "Ręczny"},
        state_key="tryb_auto_state",
        icon="mdi:state-machine",
        enabled=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PelloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PelloSelect(coordinator, definition) for definition in SELECTS)


class PelloSelect(PelloEntity, SelectEntity):
    """Wybór trybu zapisywany przez setregister.cgi."""

    def __init__(self, coordinator: PelloCoordinator, definition: PelloSelectDef) -> None:
        super().__init__(coordinator, definition.key, definition.name)
        self._def = definition
        if definition.unique_suffix:
            self._attr_unique_id = f"{UNIQUE_ID_PREFIX}_{definition.unique_suffix}"
        self._attr_options = list(definition.options.values())
        self._attr_icon = definition.icon
        self._attr_entity_registry_enabled_default = definition.enabled

    @property
    def current_option(self) -> str | None:
        raw = self._raw(self._def.state_key or self._def.key)
        if raw is None:
            return None
        return self._def.options.get(raw)

    async def async_select_option(self, option: str) -> None:
        value = next(raw for raw, label in self._def.options.items() if label == option)
        await self.coordinator.async_write(self._def.key, value)
