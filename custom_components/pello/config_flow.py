import logging
import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_USERNAME, default="root"): str,
    vol.Optional(CONF_PASSWORD): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
})

class PelloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Obsługa konfiguracji z poziomu interfejsu HA."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok wywoływany przez użytkownika z UI."""
        errors = {}

        if user_input is not None:
            valid = await self._test_connection(
                user_input[CONF_HOST],
                user_input.get(CONF_USERNAME),
                user_input.get(CONF_PASSWORD)
            )

            if valid:
                return self.async_create_entry(
                    title=f"Piec Pello ({user_input[CONF_HOST]})", 
                    data=user_input
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )

    async def _test_connection(self, host, username, password):
        """Sprawdza, czy sterownik odpowiada na podane dane logowania."""
        url = f"http://{host}/syncvalues.cgi"
        auth = aiohttp.BasicAuth(username, password) if username and password else None
        
        try:
            session = async_get_clientsession(self.hass)
            async with async_timeout.timeout(10):
                async with session.get(url, auth=auth) as response:
                    return response.status == 200
        except Exception as e:
            _LOGGER.error(f"Pello test connection error: {e}")
            return False