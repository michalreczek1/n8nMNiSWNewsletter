# n8n MNiSW Newsletter

Newsletter workflow based on `n8n` that:
- reads the latest legislative projects from RCL,
- extracts justification documents from the active stage,
- generates AI summaries and key changes,
- sends a daily newsletter through Resend.

Repository target:
- GitHub: `https://github.com/michalreczek1/n8nMNiSWNewsletter`

## Architecture

Preferred deployment architecture for Railway:
- one custom Railway service,
- `n8n` and the Python helper running inside the same container,
- local communication from `n8n` to the helper via `127.0.0.1:8765`,
- persistent `n8n` data stored on a Railway Volume mounted to `/home/node/.n8n`.

Why this is the preferred shape:
- no extra service discovery,
- no need to change the current helper URL in the workflow,
- simpler operational model for a single maintainer.

## Repository Contents

- [RPL.json](E:/Projects/n8n/RPL.json)
- `RPL.json`
  Main workflow export.
- `scripts/rcl_extract_service.py`
  Local HTTP helper used by the workflow.
- `scripts/rcl_extract_project.py`
  RCL parser that fetches the active stage and extracts project content.
- `Dockerfile`
  Runtime image for Railway.
- `start.sh`
  Container start script that launches the helper and `n8n`.
- `requirements.txt`
  Python dependencies for the helper.

## Local Development

### 1. Python helper
Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the helper:

```bash
python scripts/rcl_extract_service.py
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

### 2. n8n
Run `n8n` locally as you do today and import `RPL.json` if needed.

## Railway Deployment

### Runtime assumptions
- deployment uses the `Dockerfile` from this repository,
- helper starts automatically inside the same container,
- `n8n` remains the public web service,
- workflow schedule is handled by the existing `Schedule Daily 07:10` node.

### Required Railway setup

1. Create or connect the Railway project.
2. Mount a persistent volume to:

```text
/home/node/.n8n
```

3. Set the required environment variables.
4. Import the workflow into `n8n`.
5. Recreate or import credentials inside `n8n`.
6. Run a full end-to-end test send.

### Required environment variables

Core `n8n`:

```text
N8N_PORT
N8N_HOST
N8N_PROTOCOL
N8N_EDITOR_BASE_URL
WEBHOOK_URL
N8N_PROXY_HOPS=1
N8N_ENCRYPTION_KEY
GENERIC_TIMEZONE=Europe/Warsaw
TZ=Europe/Warsaw
```

Helper:

```text
RCL_HELPER_HOST=127.0.0.1
RCL_HELPER_PORT=8765
```

Secrets used by integrations or credentials:

```text
Resend API key
Groq API key
```

Notes:
- credentials are stored by `n8n`, so they must exist in the deployed instance,
- `N8N_ENCRYPTION_KEY` must stay stable after the first deployment.

## Suggested Railway Flow

### Option A: GitHub-first
- push this repository to GitHub,
- create a Railway project from the GitHub repo,
- attach a volume,
- configure env vars,
- deploy and import the workflow.

### Option B: Railway CLI
- initialize or link the Railway project with CLI,
- deploy from the current directory after the repo is in place,
- complete env and volume configuration in Railway.

## Operational Notes

- This repo should never include your local `n8n` database or credential exports containing secrets.
- The workflow currently assumes the helper is available at `127.0.0.1:8765`; this is intentional for the single-service deployment model.
- If you later split the helper into a separate Railway service, the helper URL in the workflow will need to be changed.

## Next Milestone Steps

Phase 4 prepares the repository and deployment bootstrap.

Phase 5 should handle:
- actual Railway environment configuration,
- linking or creating the service,
- persistent storage setup,
- first deployment path validation.
