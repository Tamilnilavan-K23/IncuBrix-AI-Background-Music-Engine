# IncuBrix Audio Studio frontend

React + Vite UI for the local FastAPI service in `../backend`. The Vite development server proxies `/api`, `/health`, and `/ready` to `http://127.0.0.1:8000`.

## Run locally

Start the backend in one PowerShell window:

```powershell
cd 'F:\incubrix\Main\version 1\backend'
.\incubrix_env\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another PowerShell window:

```powershell
cd 'F:\incubrix\Main\version 1\frontend'
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://127.0.0.1:5173/`). If that port is occupied, Vite automatically selects the next available port. Build the production assets with `npm run build`.

The app submits music jobs, polls their status, reads the manifest, plays the mix or a stem, and offers WAV downloads. The visible generator disclosure matches the backend: the output is procedural symbolic composition, not neural text-to-music. Audio-quality measurements absent from the backend are not presented as passed.
