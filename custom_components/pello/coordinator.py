"""Komunikacja ze sterownikiem Pello i koordynator odświeżania."""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from urllib.parse import unquote
from xml.etree import ElementTree

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from yarl import URL

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEVICE_NAME,
    DOMAIN,
    MAIN_DEVICE,
    MANUFACTURER,
    MODEL,
    PATH_VALUES,
    PATH_WRITE,
    REQUEST_TIMEOUT,
    SECRET_PREFIXES,
)

_LOGGER = logging.getLogger(__name__)

_REGISTER_ID = re.compile(r"^[A-Za-z0-9_]+$")
_REGISTER_VALUE = re.compile(r"^-?\d+(\.\d+)?$")

type PelloConfigEntry = ConfigEntry[PelloCoordinator]


class PelloAuthError(Exception):
    """Sterownik odrzucił login lub hasło."""


class PelloConnectionError(Exception):
    """Brak połączenia lub niepoprawna odpowiedź sterownika."""


def parse_syncvalues(text: str) -> dict[str, str]:
    """Parsuje pierwszą linię syncvalues.cgi (główne urządzenie) do słownika.

    Format: ``0;<czas>;s:1;klucz:wartość;klucz:wartość;...``. Wartości są
    zakodowane URL-em (np. ``396m%2034s``). Klucze ``auth_*`` są pomijane.
    """
    first_line = text.lstrip("﻿").split("\n", 1)[0].strip()
    data: dict[str, str] = {}
    for item in first_line.split(";"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        if not _REGISTER_ID.match(key) or key.startswith(SECRET_PREFIXES):
            continue
        data[key] = unquote(value)
    return data


def _check_write_response(text: str, key: str) -> None:
    """Sprawdza odpowiedź setregister.cgi.

    Sterownik odpowiada XML-em ``<cmd status="ok"><device><reg tid=".." status="ok"/>``.
    Jeśli odpowiedzi nie da się sparsować (inna wersja oprogramowania), uznajemy
    zapis za udany — o wyniku i tak przesądzi kolejny odczyt.
    """
    try:
        root = ElementTree.fromstring(text.lstrip("﻿").strip())
    except ElementTree.ParseError:
        _LOGGER.debug("Nieoczekiwana odpowiedź setregister.cgi dla %s: %.200s", key, text)
        return

    if (root.get("status") or "ok") != "ok":
        raise HomeAssistantError(
            f"Sterownik odrzucił zapis {key} (status: {root.get('status')})"
        )
    for reg in root.iter("reg"):
        if reg.get("tid") == key:
            status = reg.get("status") or "ok"
            if status != "ok":
                raise HomeAssistantError(
                    f"Sterownik nie zmienił rejestru {key} (status: {status})"
                )
            return


class PelloCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Odczytuje syncvalues.cgi i zapisuje rejestry przez setregister.cgi."""

    config_entry: PelloConfigEntry

    def __init__(self, hass: HomeAssistant, entry: PelloConfigEntry) -> None:
        interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(interval)),
        )
        self.host: str = entry.data[CONF_HOST]
        username = entry.data.get(CONF_USERNAME) or ""
        password = entry.data.get(CONF_PASSWORD) or ""
        self._auth = aiohttp.BasicAuth(username, password) if username else None
        self._session = async_get_clientsession(hass)
        self._base = URL.build(scheme="http", host=self.host)

    async def _request(self, path: str, query: dict[str, str | int] | None = None) -> str:
        url = self._base / path
        if query is not None:
            url = url.with_query(query)
        try:
            async with self._session.get(
                url,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                if response.status in (401, 403):
                    raise PelloAuthError
                if response.status != 200:
                    raise PelloConnectionError(f"{path}: HTTP {response.status}")
                return await response.text(errors="replace")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PelloConnectionError(f"{path}: {err}") from err

    async def _async_update_data(self) -> dict[str, str]:
        try:
            text = await self._request(PATH_VALUES)
        except PelloAuthError as err:
            raise ConfigEntryAuthFailed("Sterownik odrzucił login lub hasło") from err
        except PelloConnectionError as err:
            raise UpdateFailed(f"Brak połączenia z piecem Pello: {err}") from err

        data = parse_syncvalues(text)
        if not data:
            raise UpdateFailed("Pusta lub niepoprawna odpowiedź syncvalues.cgi")
        return data

    async def async_write(self, key: str, value: str) -> None:
        """Zapisuje jeden rejestr i odświeża dane."""
        if not _REGISTER_ID.match(key) or not _REGISTER_VALUE.match(value):
            raise HomeAssistantError(f"Niepoprawny zapis: {key}={value}")
        try:
            # Sterownik wymaga kolejności: najpierw device, potem rejestr.
            text = await self._request(PATH_WRITE, {"device": MAIN_DEVICE, key: value})
        except PelloAuthError as err:
            raise HomeAssistantError("Sterownik odrzucił login lub hasło") from err
        except PelloConnectionError as err:
            raise HomeAssistantError(f"Nie udało się zapisać {key}: {err}") from err

        _check_write_response(text, key)
        _LOGGER.info("Pello: ustawiono %s=%s", key, value)
        await self.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        data = self.data or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=data.get("device_soft_version") or None,
            hw_version=data.get("device_hard_version") or None,
            serial_number=data.get("device_sn") or None,
            configuration_url=f"http://{self.host}/",
        )
