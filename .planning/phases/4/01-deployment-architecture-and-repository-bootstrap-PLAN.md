---
phase: 4
title: Deployment architecture and repository bootstrap
slug: deployment-architecture-and-repository-bootstrap
status: planned
owner: Codex
depends_on:
  - milestone-v1.1-initialization
outputs:
  - GitHub-ready project structure
  - Railway deployment bootstrap files
  - documented single-service deployment architecture
verification:
  - repository contains all required deployment assets
  - Railway runtime assumptions are explicit and testable
  - handoff to phase 5 is clear and low-risk
planned_at: 2026-03-14
---

# Plan

## Objective
Przygotować projekt do wejścia na ścieżkę `GitHub -> Railway` poprzez uporządkowanie repozytorium, wybór docelowej architektury uruchomieniowej oraz dodanie podstawowych artefaktów deploymentowych.

## Success Criteria
- projekt ma strukturę gotową do wrzucenia do repo `https://github.com/michalreczek1/n8nMNiSWNewsletter`,
- istnieje jasno opisana architektura deploymentu Railway,
- obecny workflow nie wymaga niepotrzebnej przebudowy tylko po to, aby działać poza lokalnym środowiskiem,
- deployment assets są gotowe do dalszej konfiguracji w fazie 5,
- lokalna wersja projektu pozostaje działająca po zmianach bootstrapowych.

## Files Expected To Change
- `E:\Projects\n8n\RPL.json`
- `E:\Projects\n8n\scripts\rcl_extract_service.py`
- `E:\Projects\n8n\scripts\rcl_extract_project.py`
- nowe pliki bootstrapowe w katalogu głównym projektu, w szczególności:
  - `Dockerfile`
  - `requirements.txt`
  - `start.sh` lub równoważny skrypt startowy
  - `.gitignore`
  - `README.md`
  - opcjonalnie pliki konfiguracyjne pod Railway

## Execution Plan

### Step 1
Zbootstrapować projekt jako repozytorium gotowe do GitHub.

Deliverables:
- podstawowa struktura repo bez lokalnego śmiecia i artefaktów tymczasowych,
- `.gitignore` obejmujący dane `n8n`, cache, logi i pliki lokalne,
- README z krótkim opisem projektu i architektury.

Implementation notes:
- nie wrzucać do repo lokalnej bazy `n8n` ani prywatnych credentialek,
- zachować eksport workflow jako artefakt źródłowy,
- potraktować repo GitHub jako clean target do pierwszego pushu.

### Step 2
Utrwalić decyzję architektoniczną dla Railway.

Deliverables:
- opis wariantu docelowego: jeden custom service na Railway,
- uzasadnienie, dlaczego helper i `n8n` mają działać razem,
- lista kompromisów oraz wariant awaryjny dwu-serwisowy.

Implementation notes:
- preferować single-service, aby zachować `127.0.0.1:8765` i uniknąć zbędnych zmian w workflow,
- jeśli w plikach pojawi się konfiguracja URL helpera, ma ona nadal wspierać lokalny tryb pracy.

### Step 3
Przygotować minimalny runtime deploymentowy.

Deliverables:
- `Dockerfile` budujący środowisko dla `n8n` i Pythona,
- `requirements.txt` z zależnościami helpera,
- skrypt startowy uruchamiający helper HTTP i `n8n`.

Implementation notes:
- skrypt startowy ma być prosty i czytelny,
- nie dopuszczać ukrytej zależności od ręcznego odpalania helpera,
- zachować zgodność z Railway runtime.

### Step 4
Przygotować konfigurację projektu pod dane trwałe i sekretne.

Deliverables:
- jawna lista wymaganych env vars dla Railway,
- rekomendacja ścieżki trwałości danych `n8n`,
- wstępny model obsługi credentialek i sekretów po deployu.

Implementation notes:
- w fazie 4 nie trzeba jeszcze ustawiać produkcyjnych wartości,
- trzeba jednak opisać wszystkie wymagane klucze i miejsca ich użycia,
- uwzględnić `Resend`, `Groq`, URL aplikacji i timezone.

### Step 5
Ustabilizować projekt pod kątem uruchamiania w kontenerze.

Deliverables:
- brak twardych założeń Windows-only w ścieżkach i uruchomieniu helpera,
- sprawdzona możliwość uruchamiania helpera i workflow w środowisku zbliżonym do Linux/containers,
- ewentualne drobne poprawki kompatybilności.

Implementation notes:
- nie przepisywać helpera bez potrzeby,
- poprawiać tylko to, co realnie blokuje działanie poza lokalnym Windows.

### Step 6
Przygotować handoff do fazy 5.

Deliverables:
- końcowa checklista tego, co trzeba skonfigurować już w samym Railway,
- lista rzeczy do wykonania po pierwszym pushu do GitHub,
- jasne rozdzielenie: co jest gotowe po fazie 4, a co celowo przechodzi do fazy 5.

## Verification Procedure

### Automated verification
1. Sprawdzić, że wszystkie pliki bootstrapowe istnieją i są spójne.
2. Zweryfikować, że projekt nadal przechodzi lokalny test regresyjny copy i że workflow export pozostaje poprawnym JSON.
3. Jeśli zostanie dodany lokalny test runtime, uruchomić helper i potwierdzić odpowiedź health-check.

### Manual verification
1. Przejrzeć strukturę repo z perspektywy pierwszego pushu na GitHub.
2. Sprawdzić, czy dokumentacja deploymentu odpowiada na pytania:
   - co deployujemy,
   - jak to startuje,
   - jakie sekrety są potrzebne,
   - gdzie siedzą trwałe dane.
3. Potwierdzić, że architektura single-service jest zrozumiała i nie wymaga dodatkowych założeń spoza repo.

### Pass condition
Projekt jest gotowy do wejścia w fazę 5: można go umieścić w GitHub, ma bootstrap deploymentowy pod Railway i nie ma już fundamentalnej niejasności, jak `n8n` oraz helper Python mają działać razem poza lokalnym komputerem.

## Risks
- zbyt szybkie wejście w deployment bez uporządkowania repo może utrudnić późniejsze utrzymanie,
- niejawne zależności lokalne mogą wyjść dopiero podczas budowania obrazu,
- błędna decyzja architektoniczna na tym etapie może skomplikować fazę 5 i 6.

## Mitigations
- trzymać zakres fazy 4 przy bootstrapie i architekturze, bez przedwczesnej produkcyjnej konfiguracji,
- preferować prosty single-service model,
- zapisać jawnie wszystkie assumptions i punkty graniczne przed końcem fazy.

## Done Definition
Phase 4 jest zakończona, gdy projekt ma repo-ready strukturę, podstawowe pliki deploymentowe dla Railway, opisaną architekturę uruchomieniową i klarowny handoff do konfiguracji środowiska w fazie 5.
