---
phase: 3
title: Final quality review and content tuning
slug: final-quality-review-and-content-tuning
status: completed
owner: Codex
depends_on:
  - phase-1-ai-summary-pipeline
  - phase-2-newsletter-ui-copy-polish
outputs:
  - tuned AI summaries for weaker projects
  - explicit quality bar for newsletter acceptance
  - verified end-to-end send with reviewed content
verification:
  - workflow still executes through Send via Resend
  - sampled summaries meet concrete editorial criteria
  - final mail is accepted without critical content issues
completed_at: 2026-03-14
---

# Plan

## Objective
Przeprowadzić końcowy quality review newslettera i dostroić generowanie treści tak, aby gotowy mail był nie tylko poprawny technicznie i wizualnie, ale też redakcyjnie użyteczny.

## Success Criteria
- dla minimum 3-5 realnych projektów summary wskazuje autora i konkretnie opisuje zmianę lub rozwiązanie,
- co najmniej 3 próbki nie brzmią jak ogólnik lub parafraza tytułu,
- `keyChanges` są spójne z summary i nie powtarzają się bez sensu,
- pełny test workflow kończy się realnym sendem bez regresji technicznej,
- końcowy mail nie ma krytycznych uwag jakościowych po ręcznej ocenie.

## Files Expected To Change
- `E:\Projects\n8n\RPL.json`
- opcjonalnie `E:\Projects\n8n\scripts\rcl_extract_project.py`

## Execution Plan

### Step 1
Zdefiniować operacyjny standard jakości summary.

Deliverables:
- krótka checklista oceny pojedynczego opisu,
- rozróżnienie między opisem akceptowalnym a zbyt ogólnym.

Quality checklist:
- czy wiadomo, kto jest autorem,
- czy wiadomo, co projekt zmienia,
- czy wiadomo, jaki jest praktyczny sens zmiany,
- czy opis unika pustych formuł typu `wprowadza nowe rozwiązania`, jeśli można powiedzieć coś konkretniejszego.

### Step 2
Przejrzeć próbki z ostatniego realnego newslettera i wskazać słabe przypadki.

Deliverables:
- lista 3-5 projektów do oceny,
- oznaczenie próbek `good / borderline / weak`,
- lista najczęstszych wad w obecnym outputcie.

Implementation notes:
- preferować mieszany zestaw: projekt bardzo dobry, średni i słaby,
- korzystać z ostatniego realnego sendu jako podstawy oceny.

### Step 3
Dostroić prompt AI pod większą konkretność.

Deliverables:
- poprawiony prompt w node `AI Project Summary`,
- jaśniejsze wymaganie wskazywania realnej zmiany normatywnej lub operacyjnej,
- mocniejsze ograniczenie pustych ogólników.

Implementation notes:
- prompt ma dalej być krótki i stabilny,
- unikać zbyt rozbudowanych instrukcji, które zwiększą niestabilność odpowiedzi.

### Step 4
Wzmocnić post-processing jakościowy dla słabszych odpowiedzi.

Deliverables:
- dodatkowa heurystyka wykrywająca zbyt ogólne summary,
- logiczne przejście do lepszego fallbacku lub do summary zbudowanego z `keyChanges`,
- zachowanie autora i konkretu nawet przy słabym outputcie modelu.

Implementation notes:
- nie blokować wysyłki,
- poprawiać treść, nie komplikować przepływu,
- jeśli potrzebne, wykrywać frazy zbyt ogólne, np. `wprowadza nowe rozwiązania`, `ma na celu poprawę`.

### Step 5
Przeprowadzić końcowy realny send testowy.

Deliverables:
- pełna egzekucja workflow aż do `Send via Resend`,
- próbka finalnego HTML i text,
- identyfikator wysyłki i ocena jakościowa.

Implementation notes:
- nie kończyć pracy na samym `success`,
- ocenić faktyczną treść dla kilku projektów z maila.

### Step 6
Podjąć decyzję pass/fail dla gotowości jakościowej.

Deliverables:
- lista ewentualnych resztkowych problemów,
- decyzja czy newsletter jest gotowy jakościowo,
- ewentualna rekomendacja dalszej mini-fazy tylko jeśli zostaną istotne braki.

## Verification Procedure

### Automated verification
1. Uruchomić workflow lokalnie na aktualnej wersji `RPL.json`.
2. Potwierdzić, że wykonanie dochodzi do `Send via Resend`.
3. Potwierdzić, że node AI nadal zwraca poprawny shape danych.
4. Potwierdzić, że słaby output AI nie blokuje budowy maila.

### Manual verification
1. Otworzyć testowego maila po wysyłce.
2. Oceniać minimum 3-5 projektów z ostatniej listy RCL.
3. Dla każdej próbki sprawdzić:
   - autora,
   - konkretną zmianę,
   - praktyczny sens projektu,
   - brak przesadnego ogólnika.
4. Porównać `summary` z `keyChanges`, czy są spójne i wzajemnie się uzupełniają.

### Pass condition
Końcowy testowy mail jest technicznie poprawny i redakcyjnie akceptowalny: większość ocenianych próbek zawiera konkretne, użyteczne opisy, a pozostałe nie psują odbioru całego newslettera.

## Risks
- zbyt agresywne heurystyki mogą odrzucać poprawne summary,
- zbyt długi prompt może pogorszyć stabilność outputu,
- część projektów nadal może mieć słaby materiał źródłowy mimo tuningu.

## Mitigations
- iterować małymi zmianami,
- oceniać efekt tylko na realnym sendzie,
- wykorzystywać `keyChanges` jako warstwę ratunkową dla słabszych summary,
- zachować prosty fallback bez blokowania całego newslettera.

## Done Definition
Phase 3 jest zakończona, gdy po końcowym tuningu promptu i jakości summary newsletter przechodzi realny send testowy i nie ma już krytycznych uwag dotyczących jakości treści.
