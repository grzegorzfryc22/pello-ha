import logging
import aiohttp
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Konfiguracja encji wyboru na podstawie Config Flow."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PelloTrybZimaLatoSelect(coordinator)])

class PelloTrybZimaLatoSelect(CoordinatorEntity, SelectEntity):
    """Encja pozwalająca na przełączanie trybu Zima/Lato."""
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tryb pracy (Zima / Lato)"
        self._attr_unique_id = "pello_35_tryb_zima_lato"
        self._attr_icon = "mdi:theme-light-dark"
        # Definiujemy dwie dostępne opcje
        self._attr_options = ["Zima", "Lato"]
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": "Piec Pello 3.5",
            "manufacturer": "esterownik.pl",
            "model": "Pello v3.5",
            "configuration_url": f"http://{coordinator.host}/",
        }

    @property
    def current_option(self):
        """Zwraca, który tryb jest obecnie aktywny na piecu."""
        data = self.coordinator.data
        if data and "zima_lato" in data:
            return "Lato" if str(data["zima_lato"]) == "1" else "Zima"
        return None

    async def async_select_option(self, option: str) -> None:
        """Wysyła komendę zmiany trybu na wybrany przez Ciebie."""
        wartosc = "1" if option == "Lato" else "0"
        url = f"http://{self.coordinator.host}/setregister.cgi?device=0&zima_lato={wartosc}"
        auth = aiohttp.BasicAuth(self.coordinator.username, self.coordinator.password)
        
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(url, auth=auth) as response:
                response.raise_for_status()
                _LOGGER.info(f"Pomyślnie zmieniono tryb na: {option}")
                
            # Wymuszenie odświeżenia danych, by przełącznik od razu przeskoczył w aplikacji
            await self.coordinator.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error(f"Błąd podczas zmiany trybu Zima/Lato: {err}")