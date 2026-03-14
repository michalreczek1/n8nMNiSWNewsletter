---
phase: 1
title: AI summary pipeline for projects
slug: ai-summary-pipeline
status: completed
owner: Codex
depends_on: []
outputs:
  - improved project summaries with author and key changes
  - stable AI fallback path
  - verified end-to-end newsletter send
verification:
  - workflow executes to Send via Resend
  - generated summaries are content-rich for sampled projects
  - fallback summaries remain readable when AI fails
completed_at: 2026-03-14
---

# Plan

## Objective
Wdrożyć warstwę AI do streszczania projektów RCL tak, aby newsletter pokazywał konkretne informacje o projekcie, a nie tylko przeredagowany tytuł aktu.

## Success Criteria
- `summary` mówi, co projekt zmienia lub wprowadza.
- `summary` wskazuje autora / wnioskodawcę.
- dla co najmniej 3 realnych projektów opis zawiera treść merytoryczną, nie tylko parafrazę tytułu.
- przy awarii AI workflow nadal kończy się poprawnie i wysyła mail.
- końcowy mail po teście end-to-end jest jakościowo zaakceptowalny.

## Files Expected To Change
- `E:\Projects\n8n\RPL.json`
- `E:\Projects\n8n\scripts\rcl_extract_project.py`
- opcjonalnie nowy pomocniczy skrypt lub prompt artifact w `E:\Projects\n8n\scripts\`

## Execution Plan

### Step 1
Przeanalizować obecny shape danych wychodzących z lokalnego helpera i zdecydować, jaki minimalny payload ma dostać AI.

Deliverables:
- lista pól wejściowych dla AI,
- decyzja, czy AI dostaje pełny `analysisText`, czy wyselekcjonowany skrót.

Implementation notes:
- preferować czysty, krótki input,
- ograniczyć śmieci z dokumentów `.doc` / `.docx`,
- jawnie przekazać autora, typ projektu i etap.

### Step 2
Dodać krok AI do workflow po aktualnym pobraniu i oczyszczeniu treści dokumentu.

Deliverables:
- nowy node lub pod-flow AI,
- deterministyczny prompt,
- ustrukturyzowany output JSON.

Required output contract:
- `summary: string`
- `author: string`
- `keyChanges: string[]`
- `sourceQuality: string` lub równoważne pole pomocnicze

Implementation notes:
- prompt ma wymuszać język polski,
- prompt ma zakazać przepisywania samego tytułu,
- prompt ma wymagać krótkiej informacji o najważniejszych rozwiązaniach projektu.

### Step 3
Zintegrować wynik AI z obecnym pipeline’em analizy i maila.

Deliverables:
- `Finalize Project Analysis` czyta wynik AI,
- `Build Email If Any` korzysta z nowych pól,
- fallback działa, jeśli AI nie odpowie lub zwróci słabą strukturę.

Implementation notes:
- `summary` z AI ma mieć priorytet,
- heurystyczny summary pozostaje jako awaryjne źródło,
- autor z AI nie może nadpisywać pewniejszego `applicant`, jeśli AI zwróci pustą wartość.

### Step 4
Wzmocnić fallback quality.

Deliverables:
- cleaner tekstu fallbackowego,
- odrzucanie artefaktów typu binarne śmieci, rozdzielniki, tabele uwag,
- skrócone i czytelne streszczenie awaryjne.

Implementation notes:
- fallback musi brzmieć jak sensowny opis użytkowy,
- brak AI nie może zablokować sekcji końcowej newslettera.

### Step 5
Przeprowadzić walidację końcową na realnym wysyłanym mailu.

Deliverables:
- pełny test workflow aż do `Send via Resend`,
- zapis wyników jakościowych dla próbek projektów,
- decyzja pass/fail dla fazy.

Review checklist:
- czy autor projektu jest obecny,
- czy opis wymienia realne zmiany,
- czy opis nie wygląda jak tytuł przepisany innymi słowami,
- czy fallback jest czytelny,
- czy cały mail nadal się wysyła bez regresji.

## Verification Procedure

### Automated verification
1. Uruchomić cały workflow lokalnie.
2. Potwierdzić, że wykonanie dochodzi do `Send via Resend`.
3. Potwierdzić, że node AI zwraca poprawny shape danych.
4. Potwierdzić, że przy błędzie AI mail nadal się buduje.

### Manual verification
1. Otworzyć testowego maila.
2. Sprawdzić minimum 3 projekty z realnej listy RCL.
3. Dla każdego ocenić:
   - czy wiadomo, kto jest autorem,
   - czy wiadomo, jakie są kluczowe zmiany,
   - czy opis jest zwięzły i informacyjny.

### Pass condition
Co najmniej 3 przykładowe projekty mają streszczenia, które są wyraźnie lepsze od obecnego stanu i nie redukują się do samego tytułu projektu.

## Risks
- model AI może dawać zbyt ogólne odpowiedzi,
- słaby dokument wejściowy obniży jakość odpowiedzi,
- zbyt długi prompt zwiększy niestabilność i koszt,
- niektóre projekty nadal będą wymagały fallbacku.

## Mitigations
- wymusić structured output,
- trzymać wejście krótkie i czyste,
- zachować heurystyczny fallback,
- testować na mieszanym zestawie projektów: dobry dokument, słaby dokument, brak uzasadnienia.

## Done Definition
Phase 1 jest zakończona, gdy AI summary pipeline działa w produkcyjnym workflow, a końcowy mail po testowej wysyłce zawiera merytoryczne opisy projektów zamiast quasi-tytułów.
