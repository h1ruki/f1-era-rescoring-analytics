@echo off
setlocal
rem Resolve all project paths from this file, even when invoked elsewhere.
pushd "%~dp0"
if errorlevel 1 exit /b 1

rem Each visible terminal calls this same file to run its service.
if /i "%~1"=="backend" goto backend
if /i "%~1"=="frontend" goto frontend

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Missing root .venv.
    goto failure
)
if not exist "%~dp0data\f1db.db" (
    echo Missing canonical data\f1db.db. Restore the tracked database before launching.
    goto failure
)
where node.exe >nul 2>nul
if errorlevel 1 (
    echo Node.js is missing from PATH.
    goto failure
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo npm.cmd is missing from PATH.
    goto failure
)
if not exist "%~dp0apps\frontend\node_modules\.bin\vite.cmd" (
    echo Frontend dependencies are missing.
    goto failure
)
set "PYTHONPATH=%~dp0apps\backend\src"
"%~dp0.venv\Scripts\python.exe" -B -c "import fastapi, uvicorn, f1_eras.api.http"
if errorlevel 1 (
    echo Backend dependencies are unavailable.
    goto failure
)
node.exe -e "for (const name of ['vite', 'react', 'react-dom', 'plotly.js']) require.resolve(name, {paths: [process.cwd() + '/apps/frontend']})"
if errorlevel 1 (
    echo Frontend dependencies are incomplete.
    goto failure
)

echo Starting backend at http://127.0.0.1:8000
echo Starting frontend at http://127.0.0.1:5173
echo Ports 8000 and 5173 must be available. Close both service windows to stop.
start "F1 ERAs - Backend" "%ComSpec%" /d /k ""%~f0" backend"
start "F1 ERAs - Frontend" "%ComSpec%" /d /k ""%~f0" frontend"
rem Give the local servers a short startup window; errors remain visible.
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173/"
popd
exit /b 0

:backend
"%~dp0.venv\Scripts\python.exe" -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir "%~dp0apps\backend\src" --host 127.0.0.1 --port 8000
set "service_exit=%errorlevel%"
popd
exit /b %service_exit%

:frontend
pushd "%~dp0apps\frontend"
call npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
set "service_exit=%errorlevel%"
popd
popd
exit /b %service_exit%

:failure
echo Development environment is not ready.
echo See docs\SETUP.md for setup instructions.
popd
exit /b 1
