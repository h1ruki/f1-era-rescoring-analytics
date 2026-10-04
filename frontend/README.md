# F1 ERAs first frontend slice

React, TypeScript, Vite, and Plotly render the curated 2010–2013 Original Drivers
championship margins supplied by the FastAPI backend. The frontend uses the API's
plot values for chart geometry; it does not calculate points or margins.

## Run locally

Open two PowerShell terminals at the repository root. In the first, start the
read-only backend:

```powershell
& .\.venv\Scripts\python.exe -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir backend/src --host 127.0.0.1 --port 8000
```

In the second, install the lockfile dependencies if needed and start Vite:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/`. Vite proxies `/api` to the backend at
`http://127.0.0.1:8000`, so browser CORS configuration is unnecessary for this
local setup. The backend reads the repository's `f1db.db` by default; set
`F1_ERAS_DB_PATH` before launching it to select another snapshot.

## Verify

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

The build command checks TypeScript and produces `dist/`. The only charted
category is Drivers; Constructors is visibly unavailable. The only scoring
context is Original. The metric toggle selects backend-provided Championship
Margin (%) or raw Points Gap plotting values. Unsupported response items display
their API reason without a fabricated chart value.
