# Phase 3 Context

## Phase
3

## Title
End-to-end validation and content review

## Intent
Domknąć projekt jakościowo: nie tylko sprawdzić, że newsletter się wysyła, ale też doprowadzić treść opisów do poziomu akceptowalnego redakcyjnie dla realnych projektów z RCL.

## Inputs
- Faza 1 wdrożyła AI summaries i `keyChanges`.
- Faza 2 domknęła layout, copy i stopkę newslettera.
- Workflow był już realnie wysyłany przez Resend i działa technicznie.
- Nadal występują przypadki, w których `summary` brzmi zbyt ogólnie mimo poprawnego layoutu.

## Current Quality Gaps
- część opisów nadal jest zbyt ogólna i niewystarczająco osadzona w konkretnej zmianie prawnej,
- nie wszystkie summary są równie dobre dla projektów z gorszym materiałem źródłowym,
- trzeba ustalić twardy standard akceptacji jakości newslettera po pełnym sendzie.

## Current Technical Anchor
- Prompt AI jest trzymany w node `AI Project Summary` w `E:\Projects\n8n\RPL.json`.
- Post-processing jakości summary jest w `Finalize Project Analysis`.
- Finalna prezentacja treści jest budowana w `Build Email If Any`.

## Constraints
- Test ma zakończyć się realnym sendem przez Resend.
- Nie wolno pogorszyć stabilności obecnego pipeline'u.
- Zmiany powinny być punktowe i mierzalne: prompt, heurystyki jakości, ewentualnie copy wokół summary.

## Assumptions
- Miarą jakości będzie ręczna ocena minimum 3-5 projektów z ostatniej realnej listy RCL.
- Jeśli AI nadal produkuje zbyt ogólne opisy dla części projektów, dopuszczalne są dodatkowe heurystyki wzmacniające lub selektywne fallbacki.
