# Phase 4 Research

## Findings

### 1. Docelowe repo GitHub istnieje, ale jest puste
Sprawdzenie `git ls-remote` dla `https://github.com/michalreczek1/n8nMNiSWNewsletter.git` nie zwróciło żadnych referencji. To oznacza, że faza 4 może traktować repo jako czysty punkt startowy do bootstrapu projektu.

### 2. Najprostsza architektura Railway to jeden custom service
Obecny workflow woła helper Python po `127.0.0.1:8765`. Jeśli `n8n` i helper będą uruchamiane w jednym kontenerze, ten adres może pozostać bez zmian. To upraszcza deployment, zmniejsza liczbę elementów do konfiguracji i redukuje ryzyko problemów z service discovery.

Wariant dwu-serwisowy (`n8n` + helper) jest możliwy, ale wymaga:
- prywatnej komunikacji między serwisami,
- zmiany URL helpera w workflow,
- większej liczby ruchomych części do utrzymania.

### 3. Trwałość danych `n8n` jest obowiązkowa
Ponieważ projekt korzysta z lokalnej bazy `n8n`, static data workflow i credentialek, deployment bez trwałego storage nie jest akceptowalny. Faza 4 powinna więc od razu założyć:
- Railway Volume dla katalogu danych `n8n`,
- albo alternatywnie plan przejścia na zewnętrzny Postgres w kolejnych krokach.

Na tym etapie bardziej pragmatyczny wydaje się Volume, bo jest prostszy do szybkiego uruchomienia.

### 4. Schedule w n8n wymaga poprawnej strefy czasowej
Codzienny run opiera się na `Schedule Daily 07:10`, więc środowisko Railway musi mieć jawnie ustawioną strefę czasową `Europe/Warsaw`. Bez tego harmonogram może odpalać się o niewłaściwej godzinie.

### 5. Deployment wymaga jawnego pakietu runtime
Projekt ma dziś trzy warstwy uruchomieniowe:
- `n8n`,
- helper HTTP w Pythonie,
- zależność Python `python-docx`.

To oznacza potrzebę przygotowania co najmniej:
- `Dockerfile`,
- pliku zależności Pythona,
- skryptu startowego uruchamiającego oba procesy,
- dokumentacji env vars i procedury wdrożenia.

### 6. Faza 4 powinna zakończyć się artefaktami, nie tylko decyzją architektoniczną
Sama decyzja „wdrażamy na Railway” nie wystarczy. Plan wykonawczy tej fazy powinien dowieźć:
- przygotowanie repo pod GitHub,
- pliki bootstrapowe deploymentu,
- opis architektury,
- checklistę do następnej fazy konfiguracyjnej.

## Recommended Direction

### Preferred architecture
Jedna usługa Railway z custom Docker image:
- `n8n` jako główny proces,
- helper Python uruchamiany w tym samym kontenerze,
- lokalna komunikacja po `127.0.0.1:8765`,
- Railway Volume dla katalogu danych `n8n`.

### Why this is preferred
- najmniej zmian w workflow,
- najmniej zewnętrznej orkiestracji,
- najprostszy mental model utrzymaniowy,
- łatwiejsza ścieżka z pustego repo do działającego deploymentu.

## Implications For Planning
- Faza 4 powinna skupić się na bootstrap repo i architekturze single-service.
- Nie trzeba jeszcze wykonywać pełnej migracji danych produkcyjnych.
- Trzeba jednak już teraz przygotować strukturę plików tak, aby faza 5 mogła przejść bez dodatkowego przepakowywania projektu.
