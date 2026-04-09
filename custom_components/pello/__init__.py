import asyncio
import logging
import aiohttp
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
# Dodano 'Platform' do importu poniżej
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Używamy oficjalnych Enumów zamiast zwykłego tekstu
PLATFORMS = [Platform.SENSOR, Platform.SELECT]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Uruchamia integrację na podstawie danych z UI."""
    host = entry.data[CONF_HOST]
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = PelloDataUpdateCoordinator(hass, host, username, password, interval)
    
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa integrację (np. przy kliknięciu 'Usuń' w UI)."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class PelloDataUpdateCoordinator(DataUpdateCoordinator):
    """Klasa pobierająca i parsująca plik syncvalues.cgi ze sterownika Pello."""
    
    def __init__(self, hass, host, username, password, interval):
        update_interval = timedelta(seconds=interval)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self.host = host
        self.username = username
        self.password = password

    async def _async_update_data(self):
        url = f"http://{self.host}/syncvalues.cgi"
        auth = aiohttp.BasicAuth(self.username, self.password) if self.username and self.password else None
        
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url, auth=auth) as response:
                    response.raise_for_status()
                    text_data = await response.text()
                    
                    parsed_data = {}
                    main_line = text_data.split('\n')[0]
                    items = main_line.split(';')
                    
                    for item in items:
                        if ':' in item:
                            key, val = item.split(':', 1)
                            parsed_data[key] = val
                            
                    return parsed_data

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout połączenia z piecem Pello: {err}") from err
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"Błąd HTTP {err.status} od pieca Pello: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Błąd komunikacji z piecem Pello: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Nieoczekiwany błąd pieca Pello: {err}") from err