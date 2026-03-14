# Phase 5 Research

## Findings

### 1. Railway project is linked, but no service exists yet
Current CLI status:
- project: `n8nMNiSWNewsletter`
- environment: `production`
- service: `None`

To oznacza, że faza 5 musi objąć nie tylko konfigurację env vars, ale też realne utworzenie i podpięcie usługi deploymentowej.

### 2. CLI covers most runtime configuration tasks
Zebrane komendy Railway CLI pokazują, że dla fazy 5 dostępne są praktyczne operacje:
- `railway variable set`
- `railway volume add`
- `railway volume attach`
- `railway up`
- `railway service link`

To wystarcza do większości pracy wykonawczej po utworzeniu samej usługi.

### 3. Storage decision should be simplified
W poprzedniej fazie został otwarty temat Volume vs Postgres. Dla pierwszego działającego deploymentu bardziej pragmatyczne jest:
- Railway Volume dla `/home/node/.n8n`

Powody:
- mniejszy zakres zmian,
- brak migracji workflow metadata do nowego backendu,
- szybsza ścieżka do działającego codziennego schedule.

### 4. The first deployment must include stable encryption and base URLs
Bez stabilnych wartości dla:
- `N8N_ENCRYPTION_KEY`
- `N8N_EDITOR_BASE_URL`
- `WEBHOOK_URL`
- `GENERIC_TIMEZONE`

instancja może działać niestabilnie operacyjnie albo mieć problemy z credentials, harmonogramem i linkami.

### 5. Runtime success is not enough without import/bootstrap of n8n state
Sama działająca usługa nie wystarczy. Po deployu trzeba jeszcze:
- wejść do zdalnego `n8n`,
- zaimportować workflow,
- odtworzyć credentials,
- sprawdzić, czy helper odpowiada wewnątrz runtime,
- wykonać test wysyłki.

### 6. Phase 5 should prepare the environment, Phase 6 should harden and hand off
Faza 5 powinna dowieźć:
- runtime,
- storage,
- env vars,
- pierwszy deploy,
- import workflow,
- test techniczny.

Faza 6 może wtedy skupić się na:
- pełnym E2E po deployu,
- checklistach operacyjnych,
- finalnym handoffie i jakości produkcyjnej.

## Recommended Direction

### Preferred execution order
1. Create or connect Railway service for the repo.
2. Attach a Railway Volume to `/home/node/.n8n`.
3. Set required env vars and stable secrets.
4. Deploy from repo/CLI.
5. Import workflow and recreate credentials.
6. Run a first technical validation.

### Why this sequence is preferred
- minimalizuje liczbę zmiennych naraz,
- szybciej odsłania problemy build/runtime,
- oddziela problemy infrastrukturalne od samej logiki workflow.

## Implications For Planning
- Plan fazy 5 powinien być mocno operacyjny, z konkretną kolejnością działań.
- Weryfikacja musi rozróżniać:
  - sukces infrastruktury,
  - sukces `n8n`,
  - sukces workflow.
- Warto jawnie zapisać, które dane i sekrety użytkownik musi wprowadzić ręcznie, jeśli nie da się ich przenieść automatycznie.
