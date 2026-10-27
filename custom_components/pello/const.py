"""Stałe integracji Pello."""

from typing import Final

DOMAIN: Final = "pello"

DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
REQUEST_TIMEOUT: Final = 10

# Prefiks unique_id — zostaje bez zmian, żeby istniejące encje zachowały historię.
UNIQUE_ID_PREFIX: Final = "pello_35"

MANUFACTURER: Final = "esterownik.pl"
MODEL: Final = "Pello v3.5"
DEVICE_NAME: Final = "Piec Pello 3.5"

PATH_VALUES: Final = "syncvalues.cgi"
PATH_WRITE: Final = "setregister.cgi"

# Główne urządzenie sterownika (pierwsza linia syncvalues.cgi, device=0 w setregister.cgi).
MAIN_DEVICE: Final = 0

# syncvalues.cgi zwraca dane logowania wszystkich poziomów dostępu (Base64 "login:hasło").
# Nigdy ich nie przechowujemy.
SECRET_PREFIXES: Final = ("auth_",)

SERVICE_ADD_FUEL: Final = "add_fuel"
ATTR_AMOUNT: Final = "amount"
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
ADD_FUEL_MIN: Final = 1
ADD_FUEL_MAX: Final = 700
