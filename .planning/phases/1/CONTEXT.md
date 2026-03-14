# Phase 1 Context

## Phase
1

## Title
AI summary pipeline for projects

## Why This Phase Exists
Obecne streszczenia projektów są zbyt słabe jakościowo. W praktyce często:
- powtarzają tytuł aktu,
- nie pokazują sedna zmian,
- nie wskazują jasno autora projektu,
- nie pomagają szybko ocenić znaczenia projektu.

To obniża użyteczność całego newslettera, nawet jeśli technicznie workflow działa poprawnie.

## Desired Outcome
Po zakończeniu tej fazy workflow ma generować krótkie, konkretne i informacyjne opisy projektów, które:
- wskazują autora / wnioskodawcę,
- opisują najważniejsze zmiany lub rozwiązania,
- są oparte na treści uzasadnienia lub innych najlepszych dostępnych dokumentach,
- nadają się bezpośrednio do użycia w newsletterze.

## In Scope
- analiza obecnego przepływu danych do streszczeń,
- wybór sposobu integracji AI,
- przygotowanie promptu i formatu odpowiedzi,
- implementacja fallbacków,
- włączenie wyniku AI do obecnego maila.

## Out of Scope
- poprawki layoutu newslettera i stopki,
- zmiana copy sekcji i spacingów UI,
- final polish HTML/text maila.

Te elementy należą do Phase 2.

## Current Implementation Facts
- Główny workflow: `E:\Projects\n8n\RPL.json`
- Lokalny helper: `E:\Projects\n8n\scripts\rcl_extract_project.py`
- Lokalny helper HTTP: `E:\Projects\n8n\scripts\rcl_extract_service.py`
- Parser już schodzi do aktywnego etapu i próbuje pobrać `Uzasadnienie`.
- Streszczenia są dziś tworzone heurystycznie w Pythonie.
- Workflow przechodzi end-to-end i potrafi wysłać mail przez Resend.

## Key Data We Already Have Per Project
- `title`
- `applicant`
- `stage`
- `number`
- `projectType`
- `dateCreated`
- `dateUpdated`
- `analysisText`
- `documentUrl`
- `documentLabel`
- `summarySource`

## Key Risks
- AI może halucynować, jeśli dostanie zbyt mało kontekstu lub brudny tekst wejściowy.
- Nie każdy projekt ma dobre `Uzasadnienie`; czasem najlepszy dokument to OSR lub projekt aktu.
- N8n i lokalny helper muszą działać stabilnie bez wywracania całego workflow przy błędzie AI.

## Decision Target For This Phase
Zaimplementować AI summary jako kontrolowany, deterministyczny krok workflow z jasnym fallbackiem i testem końcowym na prawdziwym mailu.
