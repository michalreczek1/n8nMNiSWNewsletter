# State

## Status
Phase 5 is in progress for milestone `v1.1`. Railway runtime configuration has started, but the service is not yet confirmed healthy.

## Current Focus
Doprowadzenie usługi Railway `n8n-newsletter` do zdrowego stanu runtime i uzyskanie działającej zdalnej instancji `n8n`.

## Known Facts
- Główny workflow jest w `E:\\Projects\\n8n\\RPL.json`.
- Lokalny helper działa przez Python HTTP service.
- Workflow obecnie potrafi wysłać mail przez Resend.
- Ostatni zweryfikowany send testowy ma id `d8a57351-6972-4962-a3c2-79c0d1eee0af`.
- Pipeline został domknięty technicznie, wizualnie i jakościowo w zakresie milestone'u `v1.0`.
- Milestone został zarchiwizowany w `.planning/milestones/`.
- Commit i tag git nie zostały utworzone, ponieważ `E:\Projects\n8n` nie jest repozytorium git.
- Nowy milestone `v1.1` zakłada uporządkowanie projektu pod GitHub i deployment na Railway.
- Obecny workflow odwołuje się do helpera po `127.0.0.1:8765`, co wymaga jawnego rozwiązania deploymentowego.
- Repozytorium git zostało zainicjalizowane lokalnie i ma `origin` ustawiony na `https://github.com/michalreczek1/n8nMNiSWNewsletter.git`.
- Railway project `n8nMNiSWNewsletter` został utworzony i podlinkowany do katalogu projektu.
- Projekt ma już bootstrap deploymentowy: `Dockerfile`, `start.sh`, `requirements.txt`, README i przykładowe env vars.
- Railway service `n8n-newsletter` została utworzona i linked do projektu.
- Railway public domain to `https://n8n-newsletter-production.up.railway.app`.
- Railway Volume został utworzony i zamontowany pod `/home/node/.n8n`.
- Bazowe env vars dla runtime zostały ustawione.
- Build przeszedł do etapu runtime na własnym obrazie `Node + Python`, ale ostatni potwierdzony blocker dotyczył uprawnień / `N8N_USER_FOLDER` na volume.

## Open Decisions
- Czy po ustabilizowaniu runtime zostawić deployment sterowany przez `railway up`, czy przejść w pełni na GitHub auto-deploy.
- Czy credentials do `Resend` i `Groq` będą odtworzone ręcznie w zdalnym `n8n`, czy przygotujemy odrębny flow migracji.
- Czy jeśli obecny single-service runtime nadal będzie zbyt ciężki, przejść na wariant dwu-serwisowy (`n8n` + helper).

## Suggested Next Step
Continue `$gsd-execute-phase 5` until the Railway service is healthy, then move to remote `n8n` access and workflow import.
