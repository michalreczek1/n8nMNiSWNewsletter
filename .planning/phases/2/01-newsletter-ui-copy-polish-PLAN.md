---
phase: 2
title: Newsletter UI and copy polish
slug: newsletter-ui-copy-polish
status: completed
owner: Codex
depends_on:
  - phase-1-ai-summary-pipeline
outputs:
  - cleaner newsletter header and card layout
  - copy updated to "Najnowsze projekty w RCL"
  - footer branding with author signature
verification:
  - HTML and text versions stay semantically aligned
  - metadata spacing is readable in sampled email output
  - workflow still executes through Send via Resend
completed_at: 2026-03-14
---

# Plan

## Objective
Dopracować warstwę wizualną i copy newslettera, aby gotowy mail wyglądał profesjonalnie, miał lepszy rytm informacji i spójnie prezentował projekty po wdrożeniu AI.

## Success Criteria
- kafle statystyk w nagłówku są wyraźnie rozdzielone i nie zlewają się wizualnie,
- sekcja końcowa używa nazwy `Najnowsze projekty w RCL` w HTML i plain text,
- data i autor/wnioskodawca są czytelnie rozdzieleni w każdej karcie projektu,
- stopka zawiera nazwę newslettera oraz podpis `Made by Michał Reczek`,
- testowy mail po wysyłce wygląda spójnie i nie ma oczywistych problemów z odstępami.

## Files Expected To Change
- `E:\Projects\n8n\RPL.json`

## Execution Plan

### Step 1
Przeprojektować hero i sekcję liczników w nagłówku.

Deliverables:
- lepszy spacing między blokiem copy a statystykami,
- wyraźniejszy odstęp między dwoma kaflami liczników,
- subtelniejsze odcięcie kafli od tła hero.

Implementation notes:
- nie zmieniać informacji, tylko ich układ i czytelność,
- zachować prosty, mail-safe HTML/CSS inline,
- sprawdzić mobile fallback przy `flex-wrap`.

### Step 2
Ujednolicić copy sekcji końcowej.

Deliverables:
- zmiana nagłówka z `Wszystkie projekty widoczne w RCL` na `Najnowsze projekty w RCL`,
- odpowiednik tej zmiany w wersji tekstowej,
- spójne copy w opisie sekcji głównej i sekcji końcowej.

Implementation notes:
- copy ma być krótkie i naturalne,
- nie używać dwóch różnych nazw dla tej samej sekcji.

### Step 3
Poprawić layout kart projektów i metadanych.

Deliverables:
- bardziej czytelny rząd metadanych w sekcji głównej,
- poprawiony odstęp między datą a autorem/wnioskodawcą,
- ten sam standard spacingu w sekcji `Najnowsze projekty w RCL`.

Implementation notes:
- zachować separator wizualny między metadanymi,
- pilnować, by w HTML nie powstawały sklejone ciągi typu `13-03-2026Minister Zdrowia`,
- dopasować wysokość linii i marginesy do dłuższych nazw resortów.

### Step 4
Dodać stopkę z brandingiem i danymi autora.

Deliverables:
- nazwa newslettera / monitora w stopce,
- podpis `Made by Michał Reczek`,
- dane autora w przyjętym formacie.

Implementation notes:
- domyślnie użyć `michalreczek@gmail.com`, jeśli użytkownik nie poda innej preferencji,
- stopka ma być lekka wizualnie i nie odciągać uwagi od treści projektów.

### Step 5
Zachować spójność HTML i plain text.

Deliverables:
- zaktualizowane etykiety i copy w obu wersjach,
- sensowny układ tekstowej reprezentacji metadanych i stopki.

Implementation notes:
- plain text nie ma odwzorowywać layoutu 1:1, ale ma przekazywać te same informacje,
- podpis autora ma pojawić się także w wersji tekstowej.

### Step 6
Przeprowadzić końcową walidację na realnym mailu.

Deliverables:
- pełny przebieg workflow aż do `Send via Resend`,
- ocena gotowego HTML i text po wysyłce,
- decyzja pass/fail dla fazy.

Review checklist:
- czy nagłówek wygląda czytelniej niż wcześniej,
- czy sekcja końcowa ma poprawną nazwę,
- czy metadane kart nie zlewają się,
- czy stopka zawiera branding i podpis autora,
- czy mail nadal dochodzi bez regresji technicznej.

## Verification Procedure

### Automated verification
1. Uruchomić workflow lokalnie na aktualnej wersji `RPL.json`.
2. Potwierdzić, że wykonanie dochodzi do `Send via Resend`.
3. Potwierdzić, że `Build Email If Any` generuje poprawny `html` i `text`.

### Manual verification
1. Otworzyć testowego maila po wysyłce.
2. Sprawdzić nagłówek, sekcję końcową i stopkę.
3. Obejrzeć minimum 3 karty projektów z dłuższymi nazwami resortów lub tytułów.
4. Potwierdzić, że metadane i odstępy są czytelne na desktopie i w zwężonym widoku.

### Pass condition
Mail po testowej wysyłce jest czytelny wizualnie, ma poprawione copy i nie zawiera zlewających się elementów w nagłówku ani w metadanych kart.

## Risks
- zbyt agresywne zmiany layoutu mogą pogorszyć renderowanie w klientach pocztowych,
- HTML i text mogą się rozjechać semantycznie,
- drobne poprawki spacingu mogą wymagać kilku iteracji po realnym sendzie.

## Mitigations
- używać prostych inline styles kompatybilnych z email HTML,
- weryfikować finalny mail po realnej wysyłce,
- trzymać wszystkie zmiany copy w jednym node, aby łatwo sprawdzić spójność.

## Done Definition
Phase 2 jest zakończona, gdy newsletter ma poprawione copy i layout, stopka zawiera branding autora, a testowy send potwierdza brak regresji wizualnej i technicznej.
