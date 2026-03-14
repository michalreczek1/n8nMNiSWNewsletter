# Phase 2 Context

## Phase
2

## Title
Newsletter UI and copy polish

## Intent
Poprawić warstwę prezentacyjną newslettera tak, aby po wdrożeniu AI opisy były podane w czytelnym, spójnym i dopracowanym layoucie.

## Inputs
- Faza 1 została zakończona i zweryfikowana end-to-end.
- Aktualny HTML i text maila są składane w node `Build Email If Any` w `E:\Projects\n8n\RPL.json`.
- Użytkownik wskazał konkretne problemy UX i copy:
  - kafle statystyk w nagłówku zlewają się,
  - sekcja końcowa powinna nazywać się `Najnowsze projekty w RCL`,
  - data i autor/wnioskodawca potrzebują czytelnego separatora i odstępu,
  - stopka ma zawierać branding i podpis `Made by Michał Reczek`.

## Current Technical Anchor
- Główna logika renderowania newslettera jest w node `Build Email If Any`.
- HTML i plain text są budowane z tych samych danych wejściowych.
- Metadane są obecnie renderowane helperem `renderMetaHtml`, ale copy i rytm layoutu nadal wymagają polishu.

## Constraints
- Zmiany mają być lokalne dla obecnej architektury workflow.
- HTML i text muszą pozostać spójne semantycznie.
- Należy zachować kompatybilność z wysyłką przez Resend i z lokalnym testem end-to-end.

## Assumptions
- W stopce można użyć podpisu `Made by Michał Reczek`.
- Domyślną daną kontaktową autora pozostaje `michalreczek@gmail.com`, jeśli użytkownik nie poda innej preferencji.
