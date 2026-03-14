# Phase 5 Context

## Phase
5

## Title
Railway runtime and environment configuration

## Intent
Przejść od bootstrapu repo i architektury do rzeczywistej konfiguracji uruchomieniowej Railway, tak aby projekt był gotowy do pierwszego deploymentu z trwałymi danymi, poprawnymi zmiennymi środowiskowymi i działającym harmonogramem codziennym.

## Inputs
- Faza 4 dostarczyła repo GitHub, pliki deploymentowe i dokumentację architektury.
- Repo jest już wypchnięte do:
  - `https://github.com/michalreczek1/n8nMNiSWNewsletter`
- Railway project został utworzony i linked:
  - `n8nMNiSWNewsletter`
  - `34f94002-ca4f-47fe-8d73-4db7467048af`

## Current Technical Anchor
- `Dockerfile` buduje single-service runtime dla `n8n` i helpera Python.
- `start.sh` uruchamia helper oraz `n8n` w jednym kontenerze.
- `railway.env.example` zawiera wstępny zestaw env vars.
- Workflow nadal zakłada helper pod `127.0.0.1:8765`.

## Current Gaps
- brak skonfigurowanej usługi Railway,
- brak volume dla danych `n8n`,
- brak ustawionych env vars i sekretów,
- brak zaimportowanego workflow do zdalnej instancji `n8n`,
- brak zweryfikowanego pierwszego deploymentu.

## Constraints
- trzeba zachować codzienny harmonogram w polskiej strefie czasowej,
- dane `n8n` muszą być trwałe między restartami,
- nie wolno zgubić credentialek ani złamać szyfrowania instancji przez zmianę `N8N_ENCRYPTION_KEY`,
- faza 5 ma przygotować i uruchomić runtime, ale końcowe jakościowe E2E po deployu pozostają też wejściem do fazy 6.

## Assumptions
- Preferowany storage dla tej fazy to Railway Volume, nie Postgres.
- Deployment będzie prowadzony w `production`, bez osobnego stagingu na tym etapie.
- Service creation może wymagać działania z UI Railway lub z flow połączonego z repo GitHub, jeśli CLI nie oferuje bezpośredniego create flow dla usługi.
