"""Sensory sterownika Pello."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfMass,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PelloConfigEntry, PelloCoordinator
from .entity import PelloEntity

ON_OFF = {"0": "Wył.", "1": "Wł."}

VALUE_MAPS: dict[str, dict[str, str]] = {
    "pl_status": {
        "0": "Stop",
        "1": "Rozpalanie",
        "2": "Praca",
        "3": "Wygaszanie",
        "4": "Czyszczenie",
    },
    "tryb_auto_state": {"0": "Ręczny", "1": "Automatyczny", "2": "Alarmowy"},
    "out_zaw4d": {"0": "Wyłączony", "1": "Otwierany", "2": "Zamykany"},
}


@dataclass(frozen=True, kw_only=True)
class PelloSensorDef:
    key: str
    name: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    icon: str | None = None
    category: EntityCategory | None = None
    precision: int | None = None
    kind: str = "number"  # number | map | onoff | timestamp
    enabled: bool = True


def _temp(key: str, name: str, icon: str, **kw) -> PelloSensorDef:
    return PelloSensorDef(
        key=key,
        name=name,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=icon,
        precision=1,
        **kw,
    )


def _setpoint(key: str, name: str, icon: str = "mdi:target") -> PelloSensorDef:
    return _temp(key, name, icon, category=EntityCategory.DIAGNOSTIC)


def _onoff(key: str, name: str, icon: str, enabled: bool = True) -> PelloSensorDef:
    return PelloSensorDef(
        key=key,
        name=name,
        icon=icon,
        kind="onoff",
        category=EntityCategory.DIAGNOSTIC,
        enabled=enabled,
    )


SENSORS: tuple[PelloSensorDef, ...] = (
    # Temperatury
    _temp("tzew_value", "Temperatura zewnętrzna", "mdi:thermometer"),
    _temp("tsp_value", "Temperatura spalin", "mdi:fire"),
    _temp("tkot_value", "Temperatura kotła", "mdi:heating-coil"),
    _temp("tcwu_value", "Temperatura CWU", "mdi:water-boiler"),
    _temp("twew_value", "Temperatura pokojowa", "mdi:home-thermometer"),
    _temp("tpow_value", "Temperatura powrotu", "mdi:thermometer-chevron-down"),
    _temp("t1_value", "Temperatura za zaworem", "mdi:pipe-valve"),
    # Nastawy (odczyt; zmiana przez encje number)
    _setpoint("kot_tzad", "Zadana temp. kotła"),
    _setpoint("cwu_tzad", "Zadana temp. CWU", "mdi:water-thermometer"),
    _setpoint("kot_tact", "Aktywna zadana temp. kotła"),
    _setpoint("cwu_tact", "Aktywna zadana temp. CWU", "mdi:water-thermometer"),
    _setpoint("ob1_zaw4d_tzad", "Aktywna zadana temp. za zaworem", "mdi:pipe-valve"),
    _setpoint("ob1_pok_tzad", "Zadana temp. pokojowa", "mdi:home-thermometer-outline"),
    # Paliwo i palnik
    PelloSensorDef(
        key="fuel_level",
        name="Poziom paliwa",
        unit=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:barrel",
    ),
    PelloSensorDef(
        key="pl_power_kw",
        name="Moc palnika",
        unit=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    PelloSensorDef(
        key="time_to_empty",
        name="Czas do braku paliwa",
        unit=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer-sand-empty",
    ),
    PelloSensorDef(
        key="pl_fuel_flow",
        name="Spalanie paliwa",
        unit="kg/h",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weight",
        precision=2,
    ),
    PelloSensorDef(
        key="add_fuel",
        name="Ostatni zasyp",
        unit=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        icon="mdi:basket-fill",
    ),
    PelloSensorDef(
        key="add_fuel_time",
        name="Data ostatniego zasypu",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-check",
        kind="timestamp",
    ),
    PelloSensorDef(
        key="next_fuel_time",
        name="Data następnego zasypu",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-clock",
        kind="timestamp",
    ),
    # Stany pracy
    PelloSensorDef(
        key="tryb_auto_state",
        name="Tryb pieca",
        icon="mdi:state-machine",
        kind="map",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="pl_status",
        name="Status kotła",
        icon="mdi:information-outline",
        kind="map",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="out_zaw4d",
        name="Stan zaworu 4D",
        icon="mdi:pipe-valve",
        kind="map",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="ob1_zaw4d_pos",
        name="Pozycja zaworu 4D",
        unit=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:valve",
        category=EntityCategory.DIAGNOSTIC,
    ),
    # Wyjścia
    _onoff("out_pomp1", "Pompa CO", "mdi:pump"),
    _onoff("out_cwu", "Pompa CWU", "mdi:water-pump"),
    _onoff("out_dm", "Stan dmuchawy", "mdi:fan"),
    _onoff("out_pod", "Podajnik", "mdi:screw-machine-flat-top"),
    _onoff("out_pomp2", "Pompa CO 2", "mdi:pump", enabled=False),
    _onoff("out_miesz", "Pompa mieszacza", "mdi:pump", enabled=False),
    _onoff("out_aux", "Wyjście AUX", "mdi:electric-switch", enabled=False),
    PelloSensorDef(
        key="act_dm_speed",
        name="Prędkość dmuchawy",
        unit=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan-speed-1",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="mpl_dm_rpm",
        name="Obroty dmuchawy",
        unit=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="pl_flame",
        name="Wartość płomienia",
        unit=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire-circle",
        category=EntityCategory.DIAGNOSTIC,
    ),
    _temp(
        "mpl_temp",
        "Temperatura modułu palnika",
        "mdi:thermometer",
        category=EntityCategory.DIAGNOSTIC,
    ),
    # Podajnik i kalibracja
    PelloSensorDef(
        key="pod_run_time",
        name="Czas pracy podajnika",
        unit=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer-outline",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="pl_calib_time",
        name="Czas kalibracji",
        unit=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:timer-cog-outline",
        category=EntityCategory.DIAGNOSTIC,
    ),
    PelloSensorDef(
        key="pl_calib_perf",
        name="Wartość kalibracji",
        unit=UnitOfMass.GRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        icon="mdi:weight-gram",
        category=EntityCategory.DIAGNOSTIC,
    ),
    # Alarmy
    _onoff("alarm_rozp", "Alarm rozpalanie", "mdi:alert"),
    _onoff("alarm_pod_zaplon", "Alarm podajnik zapłon", "mdi:alert-fire"),
    _onoff("alarm_tkot_90", "Alarm temp kotła", "mdi:alert-thermometer"),
    _onoff("alarm_tpod_hi", "Alarm temp podajnik", "mdi:alert-thermometer"),
    _onoff("alarm_termik", "Alarm STB (Termik)", "mdi:alert-octagon"),
    _onoff("alarm_stb", "Alarm STB", "mdi:alert-octagon"),
    _onoff("alarm_zasobnik", "Alarm zasobnika", "mdi:alert-circle"),
    _onoff("alarm_otw_zasob", "Alarm otwarty zasobnik", "mdi:archive-alert"),
    _onoff("alarm_tco1_hi", "Alarm temp. obiegu CO1", "mdi:alert-thermometer"),
    _onoff("alarm_t1", "Alarm czujnika za zaworem", "mdi:alert-circle-outline"),
    _onoff("mpl_alarm", "Alarm modułu palnika", "mdi:alert-circle"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PelloConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(PelloSensor(coordinator, definition) for definition in SENSORS)


class PelloSensor(PelloEntity, SensorEntity):
    """Pojedynczy odczyt ze sterownika."""

    def __init__(self, coordinator: PelloCoordinator, definition: PelloSensorDef) -> None:
        super().__init__(coordinator, definition.key, definition.name)
        self._def = definition
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class
        self._attr_icon = definition.icon
        self._attr_entity_category = definition.category
        self._attr_suggested_display_precision = definition.precision
        self._attr_entity_registry_enabled_default = definition.enabled

    @property
    def native_value(self) -> str | int | float | datetime | None:
        raw = self._raw()
        if raw is None:
            return None

        kind = self._def.kind
        if kind == "map":
            return VALUE_MAPS[self._key].get(raw, f"Nieznany ({raw})")
        if kind == "onoff":
            # Alarmy modułu palnika mogą zwracać kody inne niż 0/1.
            return ON_OFF.get(raw, f"Wł. ({raw})")
        if kind == "timestamp":
            try:
                seconds = float(raw)
            except ValueError:
                return None
            if seconds <= 0:
                return None
            return datetime.fromtimestamp(seconds, tz=UTC)

        try:
            value = float(raw)
        except ValueError:
            return raw
        return int(value) if value.is_integer() else value
