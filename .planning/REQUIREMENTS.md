# Requirements

## Milestone
`v1.1` - GitHub and Railway deployment for the RCL / MNiSW newsletter workflow

## Goal
Przygotować projekt do stabilnego działania poza lokalnym komputerem, tak aby newsletter wykonywał się codziennie w Railway, a cały deployment był zarządzany z repozytorium GitHub.

## Product Requirements

### 1. GitHub-ready project structure
- Projekt musi zostać uporządkowany tak, aby mógł zostać umieszczony w repozytorium GitHub.
- Repo musi zawierać wszystkie pliki potrzebne do uruchomienia deploymentu:
  - workflow export,
  - helper Python,
  - pliki deploymentowe,
  - dokumentację uruchomienia i konfiguracji.

### 2. Railway deployment architecture
- Rozwiązanie musi być wdrażalne na Railway.
- Architektura wdrożenia musi obsługiwać:
  - `n8n`,
  - helper Python do ekstrakcji treści z RCL,
  - komunikację między tymi komponentami.
- Preferowany jest wariant możliwie prosty operacyjnie, z minimalną liczbą ruchomych części.

### 3. Daily scheduled execution
- Workflow musi wykonywać się codziennie bez udziału lokalnego komputera użytkownika.
- Harmonogram ma pozostać zgodny z założeniem codziennego newslettera.
- Strefa czasowa musi być poprawnie ustawiona dla Polski.

### 4. Persistent state and credentials
- Deployment musi zachować trwałość danych `n8n` między restartami i redeployami.
- Konfiguracja musi przewidywać bezpieczne przechowywanie sekretów i credentialek.
- Utrata danych po restarcie platformy nie może być akceptowalnym trybem działania.

### 5. Operational clarity
- Projekt musi mieć prostą instrukcję:
  - jak uruchomić go lokalnie,
  - jak wdrożyć go na Railway,
  - jakie zmienne środowiskowe są wymagane,
  - jak podmienić credentials i jak wykonać test po deployu.

### 6. End-to-end verification after deployment prep
- Po przygotowaniu milestone'u ma istnieć jasna ścieżka weryfikacji:
  - test helpera,
  - test workflow,
  - test realnej wysyłki maila,
  - kontrola treści maila po wdrożeniu.

## Non-Goals
- W tym milestone nie przebudowujemy jakości treści AI poza tym, co jest potrzebne do zachowania kompatybilności deploymentu.
- W tym milestone nie zmieniamy źródła danych z `legislacja.gov.pl`.
- W tym milestone nie przenosimy projektu na inną platformę niż Railway.

## Success Criteria
- Projekt ma przygotowane artefakty deploymentowe pod Railway.
- Istnieje sensowna ścieżka `GitHub -> Railway`.
- Architektura uruchamia `n8n` i helper Python bez lokalnych zależności typu ręczne odpalanie usług.
- Dane `n8n` są trwałe między restartami.
- Po wdrożeniu możliwy jest codzienny automatyczny run workflow.

## Constraints
- Obecny workflow bazuje na helperze HTTP i nie może utracić tej funkcjonalności.
- Obecne credentialki i workflow nie mogą zostać przypadkowo uszkodzone podczas przygotowania deploymentu.
- Rozwiązanie powinno być możliwie proste do utrzymania przez jedną osobę.

## Open Questions
- Czy Railway ma być środowiskiem jedynym, czy najpierw staging i potem production.
- Czy docelowo dane `n8n` mają siedzieć na Railway Volume czy w zewnętrznym Postgresie.
- Czy repo GitHub ma być prywatne od początku.
