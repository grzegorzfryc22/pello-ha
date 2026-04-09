import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, UnitOfMass, UnitOfTime, PERCENTAGE, EntityCategory
from .const import DOMAIN

# Lista: (klucz, nazwa, jednostka, klasa_urzadzenia, ikona, kategoria)
SENSORS = (
    ("tzew_value", "Temperatura zewnętrzna", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer", None),
    ("tsp_value", "Temperatura spalin", UnitOfTemperature.CELSIUS, "temperature", "mdi:fire", None),
    ("tkot_value", "Temperatura kotła", UnitOfTemperature.CELSIUS, "temperature", "mdi:heating-coil", None),
    ("tcwu_value", "Temperatura CWU", UnitOfTemperature.CELSIUS, "temperature", "mdi:water-boiler", None),
    ("twew_value", "Temperatura sypialnia", UnitOfTemperature.CELSIUS, "temperature", "mdi:home-thermometer", None),
    ("tpow_value", "Temperatura powrotu", UnitOfTemperature.CELSIUS, "temperature", "mdi:thermometer-chevron-down", None),
    ("kot_tzad", "Zadana temp. kotła", UnitOfTemperature.CELSIUS, "temperature", "mdi:target", None),
    ("cwu_tzad", "Zadana temp. CWU", UnitOfTemperature.CELSIUS, "temperature", "mdi:water-thermometer", None),
    ("fuel_level", "Poziom paliwa", PERCENTAGE, None, "mdi:barrel", None),
    ("pl_power_kw", "Moc palnika", "kW", "power", "mdi:lightning-bolt", None),
    ("time_to_empty", "Czas do braku paliwa", UnitOfTime.HOURS, None, "mdi:hourglass-empty", None),
    ("pl_fuel_flow", "Spalanie paliwa", "kg/h", None, "mdi:weight", None),

    ("tryb_auto_state", "Tryb pieca", None, None, "mdi:state-machine", EntityCategory.DIAGNOSTIC),
    ("pl_status", "Status kotła", None, None, "mdi:information-outline", EntityCategory.DIAGNOSTIC),
    ("out_pomp1", "Pompa CO", None, None, "mdi:pump", EntityCategory.DIAGNOSTIC),
    ("out_cwu", "Pompa CWU", None, None, "mdi:water-pump", EntityCategory.DIAGNOSTIC),
    ("out_dm", "Stan dmuchawy", None, None, "mdi:fan", EntityCategory.DIAGNOSTIC),
    ("act_dm_speed", "Prędkość dmuchawy", PERCENTAGE, None, "mdi:fan-speed-1", EntityCategory.DIAGNOSTIC),
    ("out_zaw4d", "Stan zaworu 4D", None, None, "mdi:pipe-valve", EntityCategory.DIAGNOSTIC),
    ("pl_flame", "Wartość płomienia", PERCENTAGE, None, "mdi:fire-circle", EntityCategory.DIAGNOSTIC),
    
    # Zmieniono klasę urządzenia na "timestamp", aby HA poprawnie formatował czas
    ("next_fuel_time", "Data następnego zasypu", None, "timestamp", "mdi:calendar-clock", EntityCategory.DIAGNOSTIC),
    
    ("pod_run_time", "Czas pracy podajnika", UnitOfTime.SECONDS, None, "mdi:timer-outline", EntityCategory.DIAGNOSTIC),
    ("pl_calib_time", "Czas kalibracji", UnitOfTime.SECONDS, None, "mdi:timer-cog-outline", EntityCategory.DIAGNOSTIC),
    ("pl_calib_perf", "Wartość kalibracji", UnitOfMass.GRAMS, None, "mdi:weight-gram", EntityCategory.DIAGNOSTIC),
    
    ("alarm_rozp", "Alarm rozpalanie", None, None, "mdi:alert", EntityCategory.DIAGNOSTIC),
    ("alarm_pod_zaplon", "Alarm podajnik zapłon", None, None, "mdi:alert-fire", EntityCategory.DIAGNOSTIC),
    ("alarm_tkot_90", "Alarm temp kotła", None, None, "mdi:alert-thermometer", EntityCategory.DIAGNOSTIC),
    ("alarm_tpod_hi", "Alarm temp podajnik", None, None, "mdi:alert-thermometer", EntityCategory.DIAGNOSTIC),
    ("alarm_termik", "Alarm STB (Termik)", None, None, "mdi:alert-octagon", EntityCategory.DIAGNOSTIC)
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Konfiguracja sensorów na podstawie Config Flow."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([
        PelloSensor(coordinator, key, name, unit, device_class, icon, category)
        for key, name, unit, device_class, icon, category in SENSORS
    ])

class PelloSensor(CoordinatorEntity, SensorEntity):
    """Reprezentacja pojedynczego sensora Pello."""
    
    def __init__(self, coordinator, key, name, unit, device_class, icon, category):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_entity_category = category
        self._attr_unique_id = f"pello_35_{key}"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": "Piec Pello 3.5",
            "manufacturer": "esterownik.pl",
            "model": "Pello v3.5",
            "configuration_url": f"http://{coordinator.host}/",
        }

    @property
    def native_value(self):
        """Zwraca obecny stan sensora."""
        data = self.coordinator.data
        if data and self._key in data:
            val = data[self._key]
            if val is not None:
                # 1. Tłumaczenie statusu pracy kotła
                if self._key == "pl_status":
                    status_map = {
                        "0": "Stop",
                        "1": "Rozpalanie",
                        "2": "Praca",
                        "3": "Wygaszanie",
                        "4": "Czyszczenie"
                    }
                    return status_map.get(str(val), f"Nieznany ({val})")

                # 2. Tłumaczenie trybu pieca
                if self._key == "tryb_auto_state":
                    tryb_map = {
                        "0": "Ręczny",
                        "1": "Automatyczny"
                    }
                    return tryb_map.get(str(val), f"Nieznany ({val})")

                # 3. Tłumaczenie zaworu 4D
                if self._key == "out_zaw4d":
                    zaw4d_map = {
                        "0": "Wyłączony",
                        "1": "Otwierany",
                        "2": "Zamykany"
                    }
                    return zaw4d_map.get(str(val), f"Nieznany ({val})")

                # 4. Tłumaczenie stanu pomp i dmuchawy
                if self._key in ["out_pomp1", "out_cwu", "out_dm"]:
                    stan_map = {
                        "0": "Wył.",
                        "1": "Wł."
                    }
                    return stan_map.get(str(val), f"Nieznany ({val})")

                # 5. Tłumaczenie wszystkich Alarmów
                if self._key.startswith("alarm_"):
                    alarm_map = {
                        "0": "Wył.",
                        "1": "Wł."
                    }
                    return alarm_map.get(str(val), f"Nieznany ({val})")

                # 6. Konwersja czasu UNIX na czytelną datę (Data zasypu)
                if self._key == "next_fuel_time":
                    try:
                        return datetime.datetime.fromtimestamp(float(val), tz=datetime.timezone.utc)
                    except ValueError:
                        return None

                # 7. Reszta sensorów (liczby zaokrąglamy)
                try:
                    return round(float(val), 1)
                except ValueError:
                    return val
        return None