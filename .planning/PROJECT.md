# Project

## Name
RCL / MNiSW Newsletter Quality Upgrade

## Objective
Podnieść jakość newslettera RCL/MNiSW tak, żeby:
- opisy projektów były tworzone przez AI na podstawie treści uzasadnień i jasno mówiły, co projekt realnie zmienia,
- mail był wizualnie dopracowany i czytelny,
- pełny przebieg był weryfikowany end-to-end aż do wysyłki i oceny treści końcowego maila.

## Current State
- Milestone `v1.0` został dostarczony i zarchiwizowany 2026-03-14.
- Workflow działa lokalnie w `n8n` i wysyła mail przez Resend.
- Dane projektów są pobierane z `legislacja.gov.pl`, a lokalny helper Python pobiera aktywny etap i dokumenty projektu.
- Newsletter generuje AI-based summaries z autorem i `keyChanges`, ma dopracowany layout oraz przechodzi realne testy wysyłki.
- Ostatni zweryfikowany send testowy ma id `d8a57351-6972-4962-a3c2-79c0d1eee0af`.
- Nowy zakres prac dotyczy produkcyjnego wdrożenia poza lokalnym środowiskiem, z preferowanym flow `GitHub -> Railway`.

## Shipped Version
- `v1.0`: AI summaries, newsletter UI/copy polish, end-to-end quality tuning, and real-send verification.

## Next Milestone Goals
- `v1.1`: przygotować projekt do wdrożenia na Railway, z repozytorium GitHub jako źródłem deploymentu, oraz zapewnić codzienne stabilne wykonywanie workflow poza lokalnym komputerem.
- Cel obejmuje deployment `n8n` wraz z helperem Python, trwałe dane, sekrety, konfigurację środowiska i procedurę operacyjną.

## Constraints
- Workflow musi działać lokalnie w obecnym `n8n`.
- Źródłem danych pozostaje `legislacja.gov.pl`, z lokalnym helperem Python.
- Trzeba zachować odporność na brak lub słabą jakość dokumentów źródłowych.
- Rozwiązanie ma wspierać realne testy wysyłki maila, nie tylko suchy render HTML.
- Aktualnie `E:\Projects\n8n` nie jest repozytorium git, więc część deploymentowa wymaga najpierw uporządkowania projektu pod GitHub.
- Workflow w obecnej postaci odwołuje się do helpera po `127.0.0.1:8765`, więc deployment wymaga świadomego opakowania `n8n` i helpera.

## Assumptions
- Dane autora do stopki: `Michał Reczek` oraz adres używany obecnie w workflow `michalreczek@gmail.com`, jeśli nie zostaną podane inne.
- Warstwa AI może być zrealizowana przez model dostępny z `n8n` bez przebudowy całej architektury workflow.
- Railway jest preferowaną platformą uruchomieniową.
- GitHub będzie źródłem deploymentu i wersjonowania zmian dla milestone'u `v1.1`.
