# Pello HA Integration
Integracja dla sterowników kotłów pelletowych **Pello v3.5** (esterownik.pl / Bero) dla Home Assistant.

## Funkcje
- 📊 Odczyt wszystkich parametrów temperatury (zewnętrzna, spaliny, kocioł, CWU, powrót).
- 📉 Monitorowanie poziomu paliwa i statystyk spalania.
- ⚡ Podgląd stanu pracy (Stop, Praca, Rozpalanie, Wygaszanie, Czyszczenie).
- ❄️/☀️ Sterowanie trybem **Zima/Lato** bezpośrednio z Home Assistant.
- 🚨 Obsługa alarmów (w tym STB Termik).

## Instalacja przez HACS
1. Otwórz HACS w Home Assistant.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Niestandardowe repozytoria**.
3. Wklej link: `https://github.com/grzegorzfryc22/pello-ha`
4. Wybierz kategorię: **Integracja**.
5. Kliknij **Dodaj**, a następnie **Pobierz**.
6. Zrestartuj Home Assistant.

## Konfiguracja
Po restarcie przejdź do **Ustawienia -> Urządzenia oraz usługi** i kliknij **Dodaj integrację**. Wyszukaj "Pello" i podaj adres IP swojego sterownika.