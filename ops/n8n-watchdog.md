# n8n: kontrola co 47 godzin

Monitor działa na hoście Proxmox, poza LXC 105 i Dockerem n8n. Wykonuje jedną
pełną kontrolę co 47 godzin. Po restarcie hosta wykonuje dodatkową kontrolę.
Nie ma osobnego zbieracza zdarzeń ani częstszego odpytywania workflow.

Mail trafia tylko do `michalreczek@gmail.com`, gdy są nieprawidłowości lub nowa
stabilna wersja n8n. Poprawne statusy nie są wysyłane. Informacja o tej samej
wersji aktualizacji jest wysyłana raz; nierozwiązane problemy mogą wrócić
w kolejnym raporcie. Monitor informuje o aktualizacjach, ale ich nie instaluje.

## Zakres

- Dostępność kontenera, gotowość n8n, zdrowie helpera i wolne miejsce w LXC.
- Aktywne workflow, ich opublikowane wersje, odwołania do poświadczeń,
  połączenia węzłów i rejestracja harmonogramów przez n8n.
- Wyłączenie/usunięcie wymaganego workflow albo pojedynczego harmonogramu.
- Produkcyjne wykonania ze statusem błędu, przerwania lub awarii, wykonania
  trwające ponad dwie godziny i oczekiwanie ponad godzinę po `waitTill`.
- Brak potwierdzonego sukcesu według harmonogramu, z tolerancją dwóch godzin.
  Reguły cron uwzględniają strefę czasową workflow i dni tygodnia. Dla
  wielodniowych interwałów kotwiczonych przez n8n sprawdzany jest maksymalny
  odstęp między sukcesami. Nieobsługiwana reguła jest raportowana jako problem
  weryfikacji; nie dostaje domyślnie poprawnego statusu.
- Dostępność nowej wersji `stable` w oficjalnym rejestrze npm; wydania
  beta/next/rc nie są zalecane jako aktualizacja produkcyjna.

Każda kontrola odczytuje istniejące metadane SQLite i istniejące logi zdarzeń.
Nie uruchamia workflow i nie modyfikuje bazy n8n. Natywne statystyki
`workflow_statistics` potwierdzają sukces także wtedy, gdy n8n nie przechowuje
pełnych poprawnych wykonań. Logi wiążą sukces z konkretną gałęzią harmonogramu.
Testy manualne i CLI nie zastępują sukcesów harmonogramu i nie są zgłaszane jako
awarie produkcji, również gdy n8n zaliczyło CLI do statystyk `production_*`.

Lista wymaganych workflow i harmonogramów jest ustalana z aktywnej konfiguracji
przy wdrożeniu. Nowe aktywne workflow również są kontrolowane. Aby kontrolować
późniejsze wyłączenie nowego workflow, należy dopisać go do `required_workflows`
i jego harmonogramy do `required_schedules`. Przed celową archiwizacją należy
usunąć go z tych list albo dodać do `ignored_workflows`. Archiwalne workflow
spoza listy wymaganych są pomijane. Zmiana nazwy harmonogramu nie usuwa go
z kontroli: polityka używa identyfikatora węzła.

Na pierwszej kontroli nowe monitorowane harmonogramy dostają czas do następnego
terminu wykonania. Dla rzadkich reguł monitor nie przedstawia braku dostępnej
historii sprzed wdrożenia jako potwierdzonej awarii. Pełna poprawność biznesowa
treści nie wynika z samego statusu `success`; monitor wykrywa opisane objawy
techniczne, bez ponownej wysyłki newsletterów i zużywania limitów modeli.

## Retencja i niezawodność

47 godzin pozostawia około godziny zapasu względem 48-godzinnej retencji
błędnych wykonań. Jeśli kontrola nie mogła działać przez 48 godzin lub dłużej,
raport ostrzega o luce w szczegółach historii. Zmiany natywnych liczników błędów
mogą nadal potwierdzić awarię po usunięciu szczegółowego wykonania.

Jedyny własny stan monitora to wynik poprzedniej kontroli: czas kontroli,
liczniki błędów, czasy sukcesów harmonogramów i identyfikatory powiadomień.
Nie jest to oddzielna historia wykonań. Dane wejściowe/wyjściowe workflow,
kody węzłów i treść poświadczeń nie są eksportowane przez sondę.

Wysyłka jest niezależna od n8n. Klucz Resend znajduje się na hoście w pliku
dostępnym tylko dla roota. Po błędzie wysyłki systemd ponawia dostarczenie
tego samego raportu co 15 minut, z tym samym kluczem idempotencji i treścią;
nie wykonuje przy tym ponownej kontroli. Stan kontroli jest zatwierdzany dopiero
po przyjęciu maila przez Resend. Awaria całego hosta Proxmox lub niedostępność
sieci uniemożliwia wysyłkę do czasu przywrócenia tych usług.

## Pliki i obsługa

Host Proxmox:

```text
/opt/n8n-watchdog/n8n_watchdog.py
/opt/n8n-watchdog/venv/
/etc/n8n-watchdog/config.json
/etc/n8n-watchdog/mail.env                 # sekret; uprawnienia 0600
/var/lib/n8n-watchdog/state.json
/var/lib/n8n-watchdog/state.outbox.json    # tylko podczas wysyłki/ponawiania
/etc/systemd/system/n8n-watchdog.service
/etc/systemd/system/n8n-watchdog.timer
```

LXC 105: `/opt/n8n-app/scripts/n8n_watchdog_probe.py` — odczyt na żądanie kontroli,
bez własnego harmonogramu lub usługi.

```bash
systemctl list-timers n8n-watchdog.timer
journalctl -u n8n-watchdog.service -n 20 --no-pager
# Kontrola diagnostyczna: bez wysyłki i bez zmiany stanu.
/opt/n8n-watchdog/venv/bin/python /opt/n8n-watchdog/n8n_watchdog.py --dry-run
# Pełna kontrola na żądanie, z warunkową wysyłką.
systemctl start n8n-watchdog.service
```

Wdrożenie wymaga `python3-venv` na hoście. Skopiuj katalogi `scripts`, `ops`
i `requirements-watchdog.txt` do katalogu wydania na hoście, uruchom
`bash ops/install-n8n-watchdog.sh`, sprawdź wynik `--dry-run`, a następnie
włącz `systemctl enable --now n8n-watchdog.timer`. Instalator zachowuje istniejącą
politykę i sekret oraz robi kopie poprzednich plików konfiguracyjnych i kodu.
Po rotacji klucza Resend trzeba również odświeżyć `mail.env` na hoście.

Walidacja lokalna, sekwencyjnie:

```powershell
python -m pip install -r requirements-watchdog.txt
python -m pytest -q
python scripts/smoke_n8n_watchdog.py
# Ze środowiska mającego Playwright; opcjonalnie wskaż zainstalowany Chrome:
$env:PLAYWRIGHT_EXECUTABLE_PATH='C:/Program Files/Google/Chrome/Application/chrome.exe'
node E:/Projects/n8n/scripts/smoke_n8n_watchdog_playwright.cjs
```

Źródła wersji i zaleceń aktualizacji:
[rejestr npm](https://registry.npmjs.org/-/package/n8n/dist-tags),
[zalecenia n8n](https://docs.n8n.io/deploy/host-n8n/keep-n8n-running/update-n8n.md).
