---
phase: 5
title: Railway runtime and environment configuration
slug: railway-runtime-and-environment-configuration
status: in_progress
owner: Codex
depends_on:
  - phase-4-deployment-architecture-and-repository-bootstrap
outputs:
  - configured Railway service
  - persistent n8n storage
  - production env vars and secret model
  - first deploy-ready runtime
verification:
  - Railway service is reachable
  - helper and n8n runtime start successfully
  - workflow can be imported and prepared for first remote execution
planned_at: 2026-03-14
---

# Plan

## Objective
Skonfigurować runtime projektu na Railway tak, aby instancja `n8n` z helperem Python mogła zostać wdrożona jako działająca, trwała i gotowa do codziennego uruchamiania usługa.

## Success Criteria
- istnieje skonfigurowana usługa Railway dla repo `n8nMNiSWNewsletter`,
- dane `n8n` są podpięte do trwałego storage,
- wszystkie wymagane env vars i sekrety są jawnie ustawione i opisane,
- pierwszy deploy startuje poprawnie,
- zdalna instancja `n8n` jest dostępna i gotowa do importu workflow,
- po fazie 5 nie ma już niejasności infrastrukturalnych blokujących końcową walidację w fazie 6.

## Files Expected To Change
- `E:\Projects\n8n\README.md`
- `E:\Projects\n8n\railway.env.example`
- opcjonalnie `E:\Projects\n8n\Dockerfile`
- opcjonalnie `E:\Projects\n8n\start.sh`
- opcjonalnie dokumentacja pomocnicza, jeśli będzie potrzebna do pierwszego deployu

## Execution Plan

### Step 1
Utworzyć lub podpiąć właściwą usługę Railway dla repozytorium.

Deliverables:
- istniejąca usługa Railway powiązana z projektem `n8nMNiSWNewsletter`,
- potwierdzony tryb deploymentu: z GitHub albo z CLI,
- lokalny katalog linked do konkretnej usługi.

Implementation notes:
- jeśli CLI nie oferuje wygodnego flow create-service, dopuszczalne jest użycie UI Railway,
- po zakończeniu kroku `railway status` nie może już pokazywać `Service: None`.

### Step 2
Skonfigurować trwałość danych `n8n`.

Deliverables:
- Railway Volume utworzony i podpięty do usługi,
- mount path ustawiony na `/home/node/.n8n`,
- potwierdzenie, że storage model dla tej fazy to Volume.

Implementation notes:
- nie przechodzić w tej fazie na Postgresa, jeśli Volume wystarcza do szybkiego, stabilnego deploymentu,
- traktować `N8N_ENCRYPTION_KEY` jako sekret wymagający trwałości razem z danymi instancji.

### Step 3
Ustawić wymagane env vars i sekrety runtime.

Deliverables:
- pełna lista ustawionych zmiennych środowiskowych dla usługi,
- stabilny `N8N_ENCRYPTION_KEY`,
- poprawnie ustawione:
  - `N8N_PORT`
  - `N8N_HOST`
  - `N8N_PROTOCOL`
  - `N8N_EDITOR_BASE_URL`
  - `WEBHOOK_URL`
  - `N8N_PROXY_HOPS`
  - `GENERIC_TIMEZONE`
  - `TZ`
  - `RCL_HELPER_HOST`
  - `RCL_HELPER_PORT`

Implementation notes:
- nie wpisywać sekretów na sztywno do repo,
- jeśli finalny publiczny URL Railway nie jest znany od razu, krok może wymagać krótkiej iteracji po pierwszym deployu,
- `RCL_HELPER_HOST` powinien pozostać `127.0.0.1` w modelu single-service.

### Step 4
Wykonać pierwszy deploy runtime na Railway.

Deliverables:
- udany deploy obrazu z repo lub przez `railway up`,
- działający start `start.sh`,
- poprawny start helpera i procesu `n8n`.

Implementation notes:
- logi startowe trzeba sprawdzić pod kątem obu procesów, nie tylko samego `n8n`,
- jeśli build/runtime pokaże problemy Linux/container-specific, naprawy nadal należą do tej fazy.

### Step 5
Przygotować zdalną instancję `n8n`.

Deliverables:
- dostęp do UI zdalnego `n8n`,
- import aktualnego workflow `RPL.json`,
- odtworzone lub skonfigurowane credentials potrzebne do działania workflow.

Implementation notes:
- w tej fazie wystarczy techniczna gotowość instancji,
- jeśli migracja credentials wymaga ręcznych kroków w UI, należy je zapisać w dokumentacji.

### Step 6
Przeprowadzić pierwszy test techniczny po deployu.

Deliverables:
- potwierdzenie, że instancja działa,
- potwierdzenie, że helper odpowiada z poziomu runtime,
- potwierdzenie, że workflow może zostać przygotowany do wykonania.

Implementation notes:
- nie trzeba jeszcze kończyć pełnym jakościowym sendem newslettera, jeśli to lepiej pasuje do fazy 6,
- trzeba jednak usunąć krytyczne blokery techniczne przed zakończeniem fazy.

### Step 7
Dopisać dokumentację operacyjną po pierwszym deployu.

Deliverables:
- README zaktualizowane o rzeczywistą ścieżkę deploymentu,
- lista ręcznych kroków potrzebnych po świeżym deployu,
- krótka checklista dla fazy 6.

## Verification Procedure

### Automated verification
1. Sprawdzić `railway status` po utworzeniu usługi.
2. Zweryfikować, że volume jest podpięty do właściwej usługi.
3. Zweryfikować, że wymagane env vars istnieją.
4. Potwierdzić, że deploy kończy się sukcesem.

### Manual verification
1. Otworzyć zdalne `n8n` po deployu.
2. Sprawdzić, czy UI ładuje się poprawnie.
3. Zaimportować workflow i potwierdzić brak oczywistych błędów w node’ach.
4. Zweryfikować, że credentials mogą zostać poprawnie ustawione.
5. Sprawdzić, czy harmonogram i strefa czasowa są zgodne z oczekiwaniami.

### Pass condition
Po fazie 5 projekt ma działającą bazową infrastrukturę na Railway: istnieje skonfigurowana usługa z trwałym storage, poprawnym runtime, ustawionymi env vars i dostępną instancją `n8n` gotową do końcowej walidacji workflow.

## Risks
- brak jednej z kluczowych zmiennych środowiskowych może pozornie uruchomić usługę, ale złamać credentials albo schedule,
- niedopasowanie publicznego URL może powodować problemy z dostępem do `n8n`,
- błędy build/runtime mogą wyjść dopiero po deployu w Railway,
- ręczne odtwarzanie credentialek może być bardziej czasochłonne niż zakładano.

## Mitigations
- weryfikować środowisko krok po kroku, nie ustawiać wszystkiego naraz bez kontroli,
- logować i dokumentować ręczne kroki w README podczas pracy,
- utrzymać single-service deployment, by ograniczyć liczbę zmiennych,
- traktować pierwszy deploy jako test infrastruktury, nie jako finalny production handoff.

## Done Definition
Phase 5 jest zakończona, gdy Railway ma już działającą usługę dla projektu, storage i env vars są ustawione, `n8n` jest dostępne po deployu, a projekt jest technicznie gotowy do końcowej walidacji workflow w fazie 6.
