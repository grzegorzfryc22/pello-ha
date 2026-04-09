import asyncio
import logging
import aiohttp

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import UnitOfTemperature, EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# (klucz_rejestru, nazwa, min, max, aktualna_nastawa_z_syncvalues)
NUMBERS = [
    ("cwu_tzad", "Zadana temperatura CWU",    10, 60),
    ("kot_tzad", "Zadana temperatura kotła CO", 30, 80),
]

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Konfiguracja encji liczb na podstawie Config Flow."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        PelloNumber(coordinator, key, name, min_val, max_val)
        for key, name, min_val, max_val in NUMBERS
    ])

class PelloNumber(CoordinatorEntity, NumberEntity):
    """Encja pozwalająca na ustawienie temperatury zadanej na piecu."""

    def __init__(self, coordinator, key, name, min_val, max_val):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"pello_35_{key}"
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = "temperature"
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:thermometer-check"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": "Piec Pello 3.5",
            "manufacturer": "esterownik.pl",
            "model": "Pello v3.5",
            "configuration_url": f"http://{coordinator.host}/",
        }

    @property
    def native_value(self):
        """Zwraca aktualną nastawę odczytaną ze sterownika."""
        data = self.coordinator.data
        if data and self._key in data:
            try:
                return float(data[self._key])
            except (ValueError, TypeError):
                return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Wysyła nową wartość do sterownika przez setregister.cgi."""
        str_value = str(int(value))
        url = (
            f"http://{self.coordinator.host}"
            f"/setregister.cgi?device=0&{self._key}={str_value}"
        )
        auth = aiohttp.BasicAuth(
            self.coordinator.username, self.coordinator.password
        ) if self.coordinator.username and self.coordinator.password else None

        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url, auth=auth) as response:
                    response.raise_for_status()
                    _LOGGER.info("Ustawiono %s na %s°C", self._key, str_value)

            await self.coordinator.async_request_refresh()

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout podczas ustawiania %s", self._key)
        except aiohttp.ClientError as err:
            _LOGGER.error("Błąd podczas ustawiania %s: %s", self._key, err)
