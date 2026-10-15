# IncuBrix AI Background Music Engine

Local FastAPI prototype. The selected backend is **local symbolic procedural synthesis**, not neural text-to-music AI. It makes three independent oscillator/percussion parts. The sound is a demonstration of the API and stem pipeline, not production music.

## Windows setup

Python 3.11 is recommended. From PowerShell:

```powershell
cd 'F:\incubrix\Main\version 1\backend'
python -m venv incubrix_env
.\incubrix_env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start one API instance with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` or `scripts\run_local.ps1` (which detects an existing local API). Do not start a second process on port 8000. Open `http://127.0.0.1:8000/docs` for interactive API docs. Run tests with `pytest -q`.

## First request

```powershell
$body = @{ prompt='Warm optimistic instrumental background'; duration_s=5; tempo_bpm=100; seed=42 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/music/jobs -Headers @{'Idempotency-Key'='demo-001'} -ContentType 'application/json' -Body $body
```

Poll `/api/v1/jobs/{job_id}`. Completed artifacts are under `data/outputs/{job_id}` and downloadable via the links in the job response.

## Design and limits

See [architecture](docs/architecture.md). Jobs and idempotency are in memory and reset on restart; the worker pool is local and not a durable queue. Files use local disk storage. Narration ducking, speech detection, actual external provider calls, exact LUFS normalization, true-peak metering, robust loop assessment, and mood-aware composition are not implemented. Their absent measurements are marked unknown; do not treat this prototype as having met the assessment's audio-quality acceptance criteria.

`docker compose up --build` runs the API. `openapi.yaml` documents the generated API contract; FastAPI serves its runtime OpenAPI 3.1 document at `/openapi.json`.
