# Phase 4 Context

## Phase
4

## Title
Deployment architecture and repository bootstrap

## Intent
Przygotować projekt do przejścia z lokalnego workflow uruchamianego ręcznie do uporządkowanego repozytorium GitHub i wdrożenia na Railway.

## Inputs
- Milestone `v1.1` dotyczy ścieżki `GitHub -> Railway`.
- Lokalny workflow działa i przechodzi realne wysyłki przez Resend.
- Projekt nie jest obecnie repozytorium git.
- Użytkownik wskazał docelowe repo GitHub:
  - `https://github.com/michalreczek1/n8nMNiSWNewsletter`

## Current Technical Anchor
- Główny workflow: `E:\Projects\n8n\RPL.json`
- Helper Python:
  - `E:\Projects\n8n\scripts\rcl_extract_service.py`
  - `E:\Projects\n8n\scripts\rcl_extract_project.py`
- Workflow woła helper po:
  - `http://127.0.0.1:8765/extract`
- Daily run opiera się na node `Schedule Daily 07:10`.

## Current Gaps
- brak repozytorium git i plików bootstrapowych pod GitHub,
- brak artefaktów deploymentowych pod Railway,
- brak jawnie opisanej architektury uruchamiania `n8n` i helpera poza środowiskiem lokalnym,
- brak procedury dla trwałych danych, sekretów i konfiguracji runtime.

## Constraints
- nie wolno zepsuć lokalnie działającego workflow,
- helper Python musi pozostać częścią rozwiązania,
- wdrożenie ma być możliwie proste do utrzymania przez jedną osobę,
- celem fazy 4 jest przygotowanie architektury i bootstrap repo, nie finalny deploy produkcyjny.

## Assumptions
- Repo GitHub jest obecnie puste i może zostać wykorzystane jako docelowe źródło deploymentu.
- Najprostszy operacyjnie wariant wdrożenia będzie preferowany nad bardziej rozproszoną architekturą.
- Railway pozostaje jedyną docelową platformą uruchomieniową dla tego milestone'u.
