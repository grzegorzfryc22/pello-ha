# Pello HA Integration

Integracja Home Assistant dla sterowników kotłów pelletowych **Pello v3.5** (esterownik.pl).
Działa lokalnie, bez chmury: odczyt przez `syncvalues.cgi`, zapis przez `setregister.cgi`.

## Funkcje

**Odczyt**
- 🌡️ Temperatury: zewnętrzna, spaliny, kocioł, CWU, powrót, pokojowa (obieg 1), **za zaworem 4D (T1)**, moduł palnika.
- 🎯 Nastawy aktywne (wyliczone przez sterownik): kocioł, CWU, za zaworem, temperatura pokojowa.
- 📉 Paliwo: poziom, spalanie (kg/h), czas do braku paliwa, **ostatni zasyp (kg i data)**, data następnego zasypu.
- ⚡ Stan pracy: status kotła (Stop / Rozpalanie / Praca / Wygaszanie / Czyszczenie), tryb (Automatyczny / Ręczny / Alarmowy), zawór 4D (stan i pozycja), pompy, podajnik, dmuchawa (% i obroty).
- 🚨 Alarmy: rozpalanie, zapłon podajnika, temperatura kotła/podajnika, STB/termik, zasobnik, otwarty zasobnik, obieg CO1, czujnik za zaworem, moduł palnika.
- Wersja oprogramowania i numer seryjny w informacjach o urządzeniu.
- Temperatury, moc i spalanie mają `state_class`, więc trafiają do statystyk długoterminowych.

**Sterowanie**
- ❄️/☀️ Tryb **Zima / Lato / Auto-lato**.
- 🚿 Tryb **CWU**: wyłączona, harmonogram, włączona, +1 h, +2 h.
- 🌡️ Temperatura zadana: **CWU** (20–60 °C), **kotła CO** (42–80 °C), **za zaworem 4D** (20–80 °C).
- 🏠 Temperatury pokojowe obiegu 1: niska / normalna / komfortowa (5–35 °C, co 0,1 °C).
- 🌦️ Regulator pogodowy kotła i obiegu za zaworem (włącz/wyłącz).
- 🛡️ **Ochrona powrotu** (pompa mieszająca / pompa CWU / zawór 4D / wyłączona), **tryb aktywacji
  ochrony powrotu** i **minimalna temperatura powrotu** (35–60 °C) — encje konfiguracyjne, patrz niżej.
- 🔕 Przycisk **Kasuj alarmy**.
- ⛽ Akcja `pello.add_fuel` — rejestracja zasypu (1–700 kg).
- ⚙️ Tryb **Automatyczny / Ręczny** — domyślnie wyłączony, patrz niżej.

Zakresy nastaw są zgodne ze słownikiem rejestrów sterownika. Wartość spoza zakresu sterownik odrzuci,
a Home Assistant pokaże błąd (nie „udaje”, że zapis się udał).

### Tryb ręczny — uwaga

Tryb ręczny **zatrzymuje palnik**, a sterownik przestaje sterować pompami, zaworem i podajnikiem —
dom i CWU przestają być grzane. Dlatego encja „Tryb sterowania (Automatyczny / Ręczny)” jest
domyślnie wyłączona. Włączysz ją w **Ustawienia → Urządzenia → Piec Pello 3.5 → encje**.
Nie używaj jej w automatyzacjach bez zabezpieczeń.

### Ochrona powrotu w trybie Lato

Gdy ochrona powrotu jest realizowana **pompą CWU**, w trybie Lato sterownik uruchamia tę pompę
także przy zatrzymanym palniku (status „Stop”), jeśli powrót spadnie poniżej minimalnej
temperatury powrotu. Zimny kocioł nie ma wtedy czym ogrzać powrotu, więc pompa pracuje ciągle
i wychładza bojler CWU. Encja „Ochrona powrotu” pozwala np. automatyzacją wyłączać ochronę
przy przejściu na Lato i przywracać ją przy przejściu na Zimę.

### Regulator pogodowy a temperatura za zaworem

Gdy regulator pogodowy obiegu jest włączony, sterownik sam wylicza temperaturę za zaworem z krzywej
grzewczej. Zmiana „Zadanej temperatury za zaworem” ma wtedy ograniczony wpływ — rzeczywistą,
wyliczoną wartość pokazuje sensor „Aktywna zadana temp. za zaworem”.

## Instalacja przez HACS
1. Otwórz HACS w Home Assistant.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Niestandardowe repozytoria**.
3. Wklej link: `https://github.com/grzegorzfryc22/pello-ha`
4. Wybierz kategorię: **Integracja**.
5. Kliknij **Dodaj**, a następnie **Pobierz**.
6. Zrestartuj Home Assistant.

## Konfiguracja
Po restarcie przejdź do **Ustawienia → Urządzenia oraz usługi → Dodaj integrację**, wyszukaj „Pello”
i podaj adres IP sterownika oraz login i hasło do jego strony WWW (zwykle `root`).
Częstotliwość odświeżania zmienisz później w **Konfiguruj** przy integracji.

## Aktualizacja z wersji 1.0.x
- Istniejące encje zachowują identyfikatory (`entity_id`) i historię.
- Nazwy wyświetlane mają teraz prefiks urządzenia („Piec Pello 3.5 …”), zgodnie ze standardem HA.
- Sensor „Temperatura CO 1” nazywa się teraz „Temperatura pokojowa” — to czujnik pokojowy obiegu 1.
- Zakres zadanej temperatury kotła to 42–80 °C (taki przyjmuje sterownik).
