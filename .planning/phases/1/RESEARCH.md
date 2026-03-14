# Phase 1 Research

## Objective
Wybrać praktyczny sposób dodania AI do streszczeń projektów w istniejącym lokalnym workflow `n8n`.

## Current Architecture
- `RPL.json` pobiera najnowsze projekty z homepage RCL.
- Lokalny helper Python pobiera szczegóły projektu i dokument z aktywnego etapu.
- `Finalize Project Analysis` liczy scoring MNiSW.
- `Build Email If Any` buduje HTML i plain text.

## Research Findings

### 1. Best insertion point for AI
Najlepszy punkt integracji AI to etap po pobraniu i oczyszczeniu treści dokumentu, a przed końcowym scoringiem i budową maila.

Praktycznie oznacza to:
- albo rozbudowę lokalnego helpera o krok AI,
- albo dodanie osobnego node’a AI po `Analyse Project & Filter`.

W tym projekcie bezpieczniejszy wydaje się drugi wariant:
- helper Python nadal odpowiada za pobranie i preprocessing źródeł,
- AI w workflow dostaje już ustrukturyzowany input,
- łatwiej testować i wymieniać model bez grzebania w parserze RCL.

### 2. Input quality matters more than long prompts
Największy wpływ na jakość podsumowań będzie mieć:
- czysty tekst z `Uzasadnienia` / OSR / projektu,
- informacja o autorze,
- typ projektu,
- numer,
- etap,
- ograniczenie długości wejścia do najważniejszych fragmentów.

Wniosek:
- nie wolno wysyłać do AI surowego, bardzo długiego `analysisText` bez selekcji,
- potrzebny jest krótki blok wejściowy z priorytetowych fragmentów.

### 3. Recommended AI output format
Najbardziej użyteczny format odpowiedzi AI dla tego workflow:
- `summary`
- `author`
- `keyChanges`
- `confidence` lub `sourceQuality` jako pole pomocnicze

Minimalny kontrakt produkcyjny:
- `summary` — 2-4 zdania
- `author` — string
- `keyChanges` — tablica 2-4 punktów

### 4. Fallback strategy
AI nie może być jedynym źródłem opisu.

Jeśli AI zawiedzie:
- zachowujemy heurystyczny `summary`,
- czyścimy go z oczywistych artefaktów,
- w mailu nadal pokazujemy projekt bez wysadzania całego runu.

### 5. Testing strategy
Faza nie jest zakończona, jeśli:
- node AI zwraca odpowiedź,
- ale końcowy mail nadal brzmi jak parafraza tytułu.

Minimalna walidacja:
- pełny send testowy,
- ręczna ocena 3-5 projektów,
- sprawdzenie czy w opisie są kluczowe zmiany i autor,
- sprawdzenie czy opis nie jest tylko rozwinięciem nagłówka projektu.

## Recommended Direction
Phase 1 powinien wdrożyć AI jako osobny etap workflow po aktualnej analizie dokumentów, z ustrukturyzowanym JSON output i mocnym fallbackiem do obecnych heurystyk.

## Open Technical Choice
Provider/model AI:
- preferowany: node lub HTTP integration już dostępna w Twoim `n8n`,
- decyzja może zostać podjęta w trakcie implementacji, ale plan powinien zostawić adapter, nie twarde sprzężenie z jednym modelem.
